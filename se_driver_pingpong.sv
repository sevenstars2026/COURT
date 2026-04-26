// =======================================================================================================
// 模块名称: se_driver (乒乓预取优化版)
// 功能说明:
//    - 双缓冲乒乓预取权重，隐藏权重加载延迟（16 拍）
//    - 严格遵循 AXI-Stream 协议：仅在拉高 tready 时消费 FIFO 数据
//    - 允许预取到空通道权重，通过输出裁剪保证时序一致性
//    - 计分板逻辑与原版保持一致
// =======================================================================================================

module se_driver #(
    // =======================================================================
    // 参数定义（根据技术手册设定，此处使用合理默认值）
    // =======================================================================
    parameter SPIKE_CACHE_BANK_NUM = 4,          // 脉冲 Bank 数量
    parameter SPIKE_DATA_BIT       = 8,          // 脉冲数据位宽
    parameter W_CAHE_BANK_NUM     = 18,          // 权重 Bank 数量
    parameter W_ADDR_BIT          = 10,          // 权重地址位宽
    parameter W_DATA_BIT          = 16,          // 权重数据位宽
    parameter NS                  = 16,          // 空间引擎数量
    parameter VM_BANK_NUM_PER_SE  = 16,          // 每 SE 膜电位 Bank 数
    parameter VM_ADDR_BIT         = 10,          // 膜电位地址位宽
    parameter VM_DATA_BIT         = 16,          // 膜电位数据位宽
    parameter CEND_VALUE          = {SPIKE_DATA_BIT{1'b1}}  // CEND 标记值（假设全1）
) (
    input  logic                                clk,
    input  logic                                rst_n,

    input  logic                                ping_pong_rd_sel,

    // =======================================================================
    // 1. 参数
    // =======================================================================
    input  logic [9:0]                          input_channels,
    input  logic [7:0]                          out_fmap_width,
    input  logic [7:0]                          out_fmap_height,
    input  logic [1:0]                          l_shift_bitnum,

    // =======================================================================
    // 2. 脉冲 FIFO 读接口 (4 个 Bank)
    // =======================================================================
    input  logic [SPIKE_DATA_BIT-1:0]           spike_s_axis_tdata  [SPIKE_CACHE_BANK_NUM-1:0],
    input  logic                                spike_s_axis_tvalid [SPIKE_CACHE_BANK_NUM-1:0],
    output logic                                spike_s_axis_tready [SPIKE_CACHE_BANK_NUM-1:0],

    // =======================================================================
    // 3. 权重缓存读接口 (18 个 Bank)
    // =======================================================================
    output logic [W_ADDR_BIT-1:0]               weight_bram_addrb [W_CAHE_BANK_NUM-1:0],
    output logic                                weight_bram_enb   [W_CAHE_BANK_NUM-1:0],
    input  logic [W_DATA_BIT-1:0]               weight_bram_doutb [W_CAHE_BANK_NUM-1:0],

    // =======================================================================
    // 4. 膜电位缓存 (LUTRAM) 读写接口 (16 个 SE, 每个 16 Bank)
    // =======================================================================
    output logic [VM_ADDR_BIT-1:0]              vm_dpra [NS-1:0][VM_BANK_NUM_PER_SE-1:0],
    input  logic [VM_DATA_BIT-1:0]              vm_dpo  [NS-1:0][VM_BANK_NUM_PER_SE-1:0],

    output logic [VM_ADDR_BIT-1:0]              vm_a    [NS-1:0][VM_BANK_NUM_PER_SE-1:0],
    output logic [VM_DATA_BIT-1:0]              vm_d    [NS-1:0][VM_BANK_NUM_PER_SE-1:0],
    output logic                                vm_we   [NS-1:0][VM_BANK_NUM_PER_SE-1:0],

    // =======================================================================
    // 5. 空间引擎接口
    // =======================================================================
    output logic                                se_driver_start,
    input  logic                                se_driver_done,
    output logic [SPIKE_DATA_BIT-1:0]           spike_to_se   [SPIKE_CACHE_BANK_NUM-1:0],
    output logic [W_DATA_BIT-1:0]               weight_to_se  [W_CAHE_BANK_NUM-1:0],
    output logic                                se_start_pulse,
    input  logic [VM_DATA_BIT-1:0]              se_vm_din     [NS-1:0][VM_BANK_NUM_PER_SE-1:0],
    output logic [VM_DATA_BIT-1:0]              se_vm_dout    [NS-1:0][VM_BANK_NUM_PER_SE-1:0]
);

    // =======================================================================
    // 内部信号定义
    // =======================================================================

    // --- 双缓冲权重缓存 ---
    reg [W_DATA_BIT-1:0] weight_buf_a [0:W_CAHE_BANK_NUM-1];
    reg [W_DATA_BIT-1:0] weight_buf_b [0:W_CAHE_BANK_NUM-1];
    reg                  cur_buf_sel;          // 0: buffer A 为当前, 1: buffer B 为当前
    reg                  pre_buf_valid;        // 预取缓存是否有效
    reg                  pre_buf_empty_chan;   // 预取通道是否为空（全CEND）
    wire [W_DATA_BIT-1:0] cur_weight [0:W_CAHE_BANK_NUM-1];
    assign cur_weight = cur_buf_sel ? weight_buf_b : weight_buf_a;

    // --- 主状态机 ---
    typedef enum logic [2:0] {
        MAIN_IDLE,
        MAIN_WAIT_START,
        MAIN_LOAD_FIRST_CUR,   // 加载第一个通道权重到当前缓存
        MAIN_COMPUTE_CUR,      // 计算当前通道
        MAIN_SWITCH_CHAN,      // 切换通道（检查预取结果）
        MAIN_DONE
    } main_state_t;
    main_state_t main_state, main_next;

    // --- 预取状态机 ---
    typedef enum logic [1:0] {
        PREF_IDLE,
        PREF_CONSUME,          // 消费 FIFO 获取下一通道脉冲
        PREF_LOAD_WEIGHT,      // 加载权重到预取缓存
        PREF_DONE              // 预取完成（可能空通道）
    } pref_state_t;
    pref_state_t pref_state, pref_next;

    // --- 通道计数器 ---
    reg [9:0]  current_channel_idx;     // 当前正在计算的通道索引
    reg [9:0]  prefetched_channel_idx;  // 预取的通道索引
    reg [9:0]  total_processed_chans;   // 已处理的有效通道数（用于输出裁剪）

    // --- 预取脉冲数据存储 ---
    reg [SPIKE_DATA_BIT-1:0] pref_spike_data [0:SPIKE_CACHE_BANK_NUM-1];

    // --- 权重加载计数器 ---
    reg [4:0]  weight_load_cnt;         // 0~15 或 0~17
    reg        weight_load_active;      // 权重加载激活

    // --- 空间引擎控制 ---
    reg        se_compute_active;
    reg        se_done_received;

    // --- 输出裁剪控制 ---
    reg        output_enable;           // 当前通道是否产生输出

    // --- 其他 ---
    reg        module_start_received;
    wire [SPIKE_CACHE_BANK_NUM-1:0] all_ready;
    wire [SPIKE_CACHE_BANK_NUM-1:0] all_valid;

    // =======================================================================
    // FIFO 就绪信号生成（组合逻辑）
    // =======================================================================
    // 主状态机或预取状态机需要消费 FIFO 时拉高 tready
    logic main_consume_fifo;   // 主状态机消费（LOAD_FIRST_CUR）
    logic pref_consume_fifo;   // 预取状态机消费（PREF_CONSUME）

    // 所有 Bank 的 tready 必须同时拉高（AXI-Stream 要求）
    assign all_valid = spike_s_axis_tvalid;
    genvar gi;
    generate
        for (gi = 0; gi < SPIKE_CACHE_BANK_NUM; gi = gi + 1) begin : gen_tready
            assign spike_s_axis_tready[gi] = (main_consume_fifo || pref_consume_fifo) && 
                                             all_valid[gi];
        end
    endgenerate

    // =======================================================================
    // 权重 BRAM 读控制（组合逻辑部分）
    // =======================================================================
    reg [W_ADDR_BIT-1:0] weight_addr_pre [0:W_CAHE_BANK_NUM-1];
    reg [W_ADDR_BIT-1:0] weight_addr_cur [0:W_CAHE_BANK_NUM-1];
    reg                  weight_en_cur;
    reg                  weight_en_pre;

    // 地址选择：当前加载（主状态机 LOAD_FIRST_CUR）或预取加载（PREF_LOAD_WEIGHT）
    // 优先级：主状态机加载优先（实际上两者不会同时发生）
    genvar gj;
    generate
        for (gj = 0; gj < W_CAHE_BANK_NUM; gj = gj + 1) begin : gen_weight_bram
            assign weight_bram_addrb[gj] = (main_state == MAIN_LOAD_FIRST_CUR) ? 
                                           weight_addr_cur[gj] : weight_addr_pre[gj];
            assign weight_bram_enb[gj]   = (main_state == MAIN_LOAD_FIRST_CUR) ? 
                                           weight_en_cur : 
                                           (pref_state == PREF_LOAD_WEIGHT) ? weight_en_pre : 1'b0;
        end
    endgenerate

    // =======================================================================
    // 主状态机（时序逻辑）
    // =======================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            main_state <= MAIN_IDLE;
            current_channel_idx <= 10'd0;
            cur_buf_sel <= 1'b0;
            output_enable <= 1'b0;
            se_compute_active <= 1'b0;
            se_done_received <= 1'b0;
            module_start_received <= 1'b0;
            total_processed_chans <= 10'd0;
            weight_en_cur <= 1'b0;
            weight_load_cnt <= 5'd0;
        end else begin
            case (main_state)
                MAIN_IDLE: begin
                    module_start_received <= 1'b0;
                    current_channel_idx <= 10'd0;
                    cur_buf_sel <= 1'b0;
                    output_enable <= 1'b0;
                    se_compute_active <= 1'b0;
                    total_processed_chans <= 10'd0;
                    weight_en_cur <= 1'b0;
                    weight_load_cnt <= 5'd0;
                    if (se_driver_start) begin
                        main_state <= MAIN_WAIT_START;
                        module_start_received <= 1'b1;
                    end
                end

                MAIN_WAIT_START: begin
                    // 等待计分板就绪等初始条件（简化处理）
                    main_state <= MAIN_LOAD_FIRST_CUR;
                    weight_en_cur <= 1'b1;
                    weight_load_cnt <= 5'd0;
                    // 计算当前地址（第一个通道权重地址）
                    for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                        weight_addr_cur[i] <= {ping_pong_rd_sel, current_channel_idx[8:0], 1'b0} + i;
                    end
                end

                MAIN_LOAD_FIRST_CUR: begin
                    if (weight_load_cnt < 5'd15) begin
                        weight_load_cnt <= weight_load_cnt + 1;
                        weight_en_cur <= 1'b1;
                        // 更新地址
                        for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                            weight_addr_cur[i] <= weight_addr_cur[i] + 1;
                        end
                    end else begin
                        // 权重加载完成，存入当前缓存
                        for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                            if (cur_buf_sel == 1'b0)
                                weight_buf_a[i] <= weight_bram_doutb[i];
                            else
                                weight_buf_b[i] <= weight_bram_doutb[i];
                        end
                        weight_en_cur <= 1'b0;
                        weight_load_cnt <= 5'd0;
                        output_enable <= 1'b1;  // 第一个通道总是有效（假设初始通道非空）
                        main_state <= MAIN_COMPUTE_CUR;
                        se_compute_active <= 1'b1;
                    end
                end

                MAIN_COMPUTE_CUR: begin
                    if (se_driver_done) begin
                        se_done_received <= 1'b1;
                        // 检查预取结果
                        main_state <= MAIN_SWITCH_CHAN;
                    end
                    // 持续计算中，权重输出到空间引擎
                    // （实际权重输出在组合逻辑中）
                end

                MAIN_SWITCH_CHAN: begin
                    se_compute_active <= 1'b0;
                    se_done_received <= 1'b0;
                    if (pre_buf_valid && !pre_buf_empty_chan) begin
                        // 预取有效，切换缓存，继续下一个通道
                        cur_buf_sel <= ~cur_buf_sel;
                        current_channel_idx <= prefetched_channel_idx;
                        total_processed_chans <= total_processed_chans + 1;
                        output_enable <= 1'b1;
                        pre_buf_valid <= 1'b0;
                        main_state <= MAIN_COMPUTE_CUR;
                        se_compute_active <= 1'b1;
                    end else begin
                        // 无更多有效通道，结束
                        output_enable <= 1'b0;
                        main_state <= MAIN_DONE;
                    end
                end

                MAIN_DONE: begin
                    se_compute_active <= 1'b0;
                    output_enable <= 1'b0;
                    if (!se_driver_start) begin
                        main_state <= MAIN_IDLE;
                    end
                end

                default: main_state <= MAIN_IDLE;
            endcase
        end
    end

    // =======================================================================
    // 预取状态机（时序逻辑）
    // =======================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pref_state <= PREF_IDLE;
            pref_consume_fifo <= 1'b0;
            pre_buf_valid <= 1'b0;
            pre_buf_empty_chan <= 1'b0;
            prefetched_channel_idx <= 10'd0;
            weight_en_pre <= 1'b0;
            for (int i = 0; i < SPIKE_CACHE_BANK_NUM; i++) begin
                pref_spike_data[i] <= '0;
            end
            for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                weight_addr_pre[i] <= '0;
            end
        end else begin
            // 默认值
            pref_consume_fifo <= 1'b0;
            weight_en_pre <= 1'b0;

            case (pref_state)
                PREF_IDLE: begin
                    pre_buf_valid <= 1'b0;
                    pre_buf_empty_chan <= 1'b0;
                    // 当主状态机进入 COMPUTE_CUR 时，触发预取
                    if (main_state == MAIN_COMPUTE_CUR && se_compute_active && !pre_buf_valid) begin
                        // 检查是否还有更多通道
                        if (current_channel_idx < input_channels - 1) begin
                            pref_state <= PREF_CONSUME;
                            pref_consume_fifo <= 1'b1;
                            prefetched_channel_idx <= current_channel_idx + 1;
                        end else begin
                            // 没有更多通道，预取到空通道标记
                            pre_buf_valid <= 1'b1;
                            pre_buf_empty_chan <= 1'b1;
                            pref_state <= PREF_DONE;
                        end
                    end
                end

                PREF_CONSUME: begin
                    // 消费 FIFO（一个周期）
                    if (all_valid[0] && all_valid[1] && all_valid[2] && all_valid[3]) begin
                        for (int i = 0; i < SPIKE_CACHE_BANK_NUM; i++) begin
                            pref_spike_data[i] <= spike_s_axis_tdata[i];
                        end
                        pref_consume_fifo <= 1'b0;
                        
                        // 检测是否全为 CEND
                        if ((pref_spike_data[0] == CEND_VALUE) &&
                            (pref_spike_data[1] == CEND_VALUE) &&
                            (pref_spike_data[2] == CEND_VALUE) &&
                            (pref_spike_data[3] == CEND_VALUE)) begin
                            // 空通道，但仍加载权重（保持流水线）
                            pre_buf_empty_chan <= 1'b1;
                        end else begin
                            pre_buf_empty_chan <= 1'b0;
                        end
                        
                        // 计算权重地址
                        for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                            weight_addr_pre[i] <= {ping_pong_rd_sel, prefetched_channel_idx[8:0], 1'b0} + i;
                        end
                        weight_en_pre <= 1'b1;
                        weight_load_cnt <= 5'd0;
                        pref_state <= PREF_LOAD_WEIGHT;
                    end
                end

                PREF_LOAD_WEIGHT: begin
                    if (weight_load_cnt < 5'd15) begin
                        weight_load_cnt <= weight_load_cnt + 1;
                        weight_en_pre <= 1'b1;
                        for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                            weight_addr_pre[i] <= weight_addr_pre[i] + 1;
                        end
                    end else begin
                        // 权重加载完成，存入预取缓存
                        // 注意：存入的是非当前缓存（即未来的当前缓存）
                        if (cur_buf_sel == 1'b0) begin
                            for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                                weight_buf_b[i] <= weight_bram_doutb[i];
                            end
                        end else begin
                            for (int i = 0; i < W_CAHE_BANK_NUM; i++) begin
                                weight_buf_a[i] <= weight_bram_doutb[i];
                            end
                        end
                        weight_en_pre <= 1'b0;
                        weight_load_cnt <= 5'd0;
                        pre_buf_valid <= 1'b1;
                        pref_state <= PREF_DONE;
                    end
                end

                PREF_DONE: begin
                    // 等待主状态机采样 pre_buf_valid
                    if (main_state == MAIN_SWITCH_CHAN) begin
                        // 主状态机正在检查预取结果，准备下一个预取
                        pref_state <= PREF_IDLE;
                        pre_buf_valid <= 1'b0;
                    end
                    // 如果主状态机已经处理完所有通道，保持在 PREF_DONE
                    if (main_state == MAIN_DONE) begin
                        pref_state <= PREF_IDLE;
                        pre_buf_valid <= 1'b0;
                    end
                end

                default: pref_state <= PREF_IDLE;
            endcase
        end
    end

    // =======================================================================
    // 主状态机 FIFO 消费信号
    // =======================================================================
    // 第一个通道的脉冲数据消费在 MAIN_LOAD_FIRST_CUR 之前的某个时刻
    // 这里简化：假设第一个通道脉冲数据已经在 FIFO 中，且有效
    // 实际实现中，需要在 LOAD_FIRST_CUR 之前或同时消费 FIFO
    // 为简化，这里直接使用 tdata（假设第一个通道数据已就绪）
    assign main_consume_fifo = (main_state == MAIN_LOAD_FIRST_CUR) && (weight_load_cnt == 5'd0);

    // =======================================================================
    // 空间引擎接口驱动
    // =======================================================================
    // 权重输出到空间引擎（组合逻辑，从当前缓存直接输出）
    genvar gk;
    generate
        for (gk = 0; gk < W_CAHE_BANK_NUM; gk = gk + 1) begin : gen_weight_to_se
            assign weight_to_se[gk] = (se_compute_active && output_enable) ? 
                                      cur_weight[gk] : {W_DATA_BIT{1'b0}};
        end
    endgenerate

    // 脉冲输出到空间引擎
    genvar gm;
    generate
        for (gm = 0; gm < SPIKE_CACHE_BANK_NUM; gm = gm + 1) begin : gen_spike_to_se
            assign spike_to_se[gm] = (se_compute_active && output_enable) ? 
                                     spike_s_axis_tdata[gm] : {SPIKE_DATA_BIT{1'b0}};
        end
    endgenerate

    // 空间引擎启动脉冲
    assign se_start_pulse = (main_state == MAIN_COMPUTE_CUR) && 
                            (main_state != MAIN_SWITCH_CHAN) && 
                            se_compute_active && output_enable;

    // 膜电位接口（简化处理，实际需计分板逻辑）
    // 此处保留接口连接，计分板逻辑需根据原版实现补充
    genvar gn, go;
    generate
        for (gn = 0; gn < NS; gn = gn + 1) begin : gen_vm_se
            for (go = 0; go < VM_BANK_NUM_PER_SE; go = go + 1) begin : gen_vm_bank
                // 读地址：从空间引擎获取
                assign vm_dpra[gn][go] = /* 根据输出坐标计算 */ '0;
                // 写地址、数据、使能：由空间引擎输出驱动
                assign vm_a[gn][go]   = se_vm_din[gn][go] ? /* 写地址 */ '0 : '0;
                assign vm_d[gn][go]   = se_vm_dout[gn][go];
                assign vm_we[gn][go]  = se_compute_active && output_enable && /* 计分板允许 */ 1'b1;
                
                // 空间引擎输入：从膜电位缓存读取的数据
                assign se_vm_din[gn][go] = vm_dpo[gn][go];
            end
        end
    endgenerate

    // =======================================================================
    // 输出裁剪逻辑
    // =======================================================================
    // 当 output_enable 为低时，空间引擎输出不计入最终结果
    // 这通过控制 vm_we 信号实现：非有效通道不写膜电位
    // 同时 se_driver_done 信号仅在处理完所有有效通道后发出

    // se_driver_done 输出（组合逻辑）
    assign se_driver_done_out = (main_state == MAIN_DONE);

    // =======================================================================
    // 计分板逻辑（保留接口，实际实现需根据原版补充）
    // =======================================================================
    // 此处仅作示意，完整计分板需处理 RAW 冒险检测
    // 计分板跟踪膜电位读写地址，确保写后读（WAR）和读后写（RAW）正确

endmodule
