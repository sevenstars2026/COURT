"""
用户头像功能测试套件
包含单元测试和集成测试，覆盖上传、获取、删除等核心功能
"""
import pytest
import os
import io
from pathlib import Path
from PIL import Image
from courtroom_web import app, courtroom_root


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def avatar_dir():
    """创建并清理测试头像目录"""
    test_avatar_dir = courtroom_root / "avatars"
    test_avatar_dir.mkdir(parents=True, exist_ok=True)
    yield test_avatar_dir
    # 清理测试文件
    for file in test_avatar_dir.glob("*"):
        if file.is_file():
            file.unlink()


@pytest.fixture
def sample_image():
    """生成测试用的图片文件"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io


@pytest.fixture
def large_image():
    """生成超过5MB的大图片"""
    img = Image.new('RGB', (3000, 3000), color='blue')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io


class TestAvatarUpload:
    """头像上传功能测试"""

    def test_upload_valid_avatar(self, client, avatar_dir, sample_image):
        """测试上传有效的头像文件"""
        data = {
            'avatar': (sample_image, 'test_avatar.png'),
            'user_id': 'test_user'
        }
        response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data['success'] is True
        assert 'avatar_url' in json_data
        assert 'test_user' in json_data['filename']
        assert json_data['size'] > 0

    def test_upload_without_file(self, client):
        """测试未选择文件时上传"""
        response = client.post('/api/avatar/upload', data={}, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data['success'] is False
        assert '未选择文件' in json_data['error']

    def test_upload_empty_filename(self, client):
        """测试空文件名"""
        data = {
            'avatar': (io.BytesIO(b''), ''),
            'user_id': 'test_user'
        }
        response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data['success'] is False
        assert '文件名为空' in json_data['error']

    def test_upload_invalid_format(self, client):
        """测试不支持的文件格式"""
        data = {
            'avatar': (io.BytesIO(b'test content'), 'test.txt'),
            'user_id': 'test_user'
        }
        response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data['success'] is False
        assert '不支持的文件格式' in json_data['error']

    def test_upload_oversized_file(self, client, large_image):
        """测试上传超过大小限制的文件"""
        data = {
            'avatar': (large_image, 'large_avatar.png'),
            'user_id': 'test_user'
        }
        response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data['success'] is False
        assert '文件过大' in json_data['error']

    def test_upload_multiple_formats(self, client, avatar_dir):
        """测试上传不同格式的图片"""
        formats = [
            ('test.png', 'PNG'),
            ('test.jpg', 'JPEG'),
            ('test.gif', 'GIF'),
            ('test.webp', 'WEBP')
        ]

        for filename, format_type in formats:
            img = Image.new('RGB', (50, 50), color='green')
            img_io = io.BytesIO()
            img.save(img_io, format_type)
            img_io.seek(0)

            data = {
                'avatar': (img_io, filename),
                'user_id': f'test_user_{format_type}'
            }
            response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 200
            assert json_data['success'] is True


class TestAvatarRetrieval:
    """头像获取功能测试"""

    def test_get_existing_avatar(self, client, avatar_dir, sample_image):
        """测试获取已存在的头像"""
        # 先上传
        data = {
            'avatar': (sample_image, 'test_avatar.png'),
            'user_id': 'test_user'
        }
        upload_response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        upload_data = upload_response.get_json()
        filename = upload_data['filename']

        # 再获取
        response = client.get(f'/api/avatar/{filename}')

        assert response.status_code == 200
        assert response.content_type.startswith('image/')

    def test_get_nonexistent_avatar(self, client):
        """测试获取不存在的头像"""
        response = client.get('/api/avatar/nonexistent_avatar.png')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data['success'] is False
        assert '头像不存在' in json_data['error']


class TestAvatarDeletion:
    """头像删除功能测试"""

    def test_delete_existing_avatar(self, client, avatar_dir, sample_image):
        """测试删除已存在的头像"""
        # 先上传
        data = {
            'avatar': (sample_image, 'test_avatar.png'),
            'user_id': 'test_user'
        }
        upload_response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        upload_data = upload_response.get_json()
        filename = upload_data['filename']

        # 再删除
        response = client.delete(f'/api/avatar/{filename}')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data['success'] is True
        assert '头像删除成功' in json_data['message']

        # 验证文件已被删除
        avatar_path = avatar_dir / filename
        assert not avatar_path.exists()

    def test_delete_nonexistent_avatar(self, client):
        """测试删除不存在的头像"""
        response = client.delete('/api/avatar/nonexistent_avatar.png')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data['success'] is False
        assert '头像不存在' in json_data['error']


class TestAvatarIntegration:
    """头像功能集成测试"""

    def test_complete_avatar_workflow(self, client, avatar_dir, sample_image):
        """测试完整的头像工作流：上传 -> 获取 -> 删除"""
        # 1. 上传头像
        data = {
            'avatar': (sample_image, 'workflow_test.png'),
            'user_id': 'workflow_user'
        }
        upload_response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
        upload_data = upload_response.get_json()

        assert upload_response.status_code == 200
        assert upload_data['success'] is True
        filename = upload_data['filename']

        # 2. 获取头像
        get_response = client.get(f'/api/avatar/{filename}')
        assert get_response.status_code == 200

        # 3. 删除头像
        delete_response = client.delete(f'/api/avatar/{filename}')
        delete_data = delete_response.get_json()
        assert delete_response.status_code == 200
        assert delete_data['success'] is True

        # 4. 验证删除后无法获取
        final_get_response = client.get(f'/api/avatar/{filename}')
        assert final_get_response.status_code == 404

    def test_multiple_users_avatars(self, client, avatar_dir):
        """测试多用户头像隔离"""
        users = ['user1', 'user2', 'user3']
        uploaded_files = []

        # 为每个用户上传头像
        for user in users:
            img = Image.new('RGB', (60, 60), color='yellow')
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)

            data = {
                'avatar': (img_io, f'{user}_avatar.png'),
                'user_id': user
            }
            response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 200
            assert user in json_data['filename']
            uploaded_files.append(json_data['filename'])

        # 验证所有头像都可以独立访问
        for filename in uploaded_files:
            response = client.get(f'/api/avatar/{filename}')
            assert response.status_code == 200

    def test_avatar_replacement(self, client, avatar_dir):
        """测试头像替换（同一用户多次上传）"""
        user_id = 'replace_test_user'
        filenames = []

        # 上传第一个头像
        img1 = Image.new('RGB', (50, 50), color='red')
        img1_io = io.BytesIO()
        img1.save(img1_io, 'PNG')
        img1_io.seek(0)

        data1 = {
            'avatar': (img1_io, 'avatar1.png'),
            'user_id': user_id
        }
        response1 = client.post('/api/avatar/upload', data=data1, content_type='multipart/form-data')
        filenames.append(response1.get_json()['filename'])

        # 上传第二个头像（替换）
        img2 = Image.new('RGB', (50, 50), color='blue')
        img2_io = io.BytesIO()
        img2.save(img2_io, 'PNG')
        img2_io.seek(0)

        data2 = {
            'avatar': (img2_io, 'avatar2.png'),
            'user_id': user_id
        }
        response2 = client.post('/api/avatar/upload', data=data2, content_type='multipart/form-data')
        filenames.append(response2.get_json()['filename'])

        # 验证两个头像都存在（系统保留历史版本）
        for filename in filenames:
            response = client.get(f'/api/avatar/{filename}')
            assert response.status_code == 200


class TestAvatarSecurity:
    """头像安全性测试"""

    def test_path_traversal_prevention(self, client):
        """测试路径遍历攻击防护"""
        malicious_filenames = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            'avatar.png/../../../secret.txt'
        ]

        for filename in malicious_filenames:
            response = client.get(f'/api/avatar/{filename}')
            # 应该返回404或400，而不是泄露系统文件
            assert response.status_code in [404, 400]

    def test_file_extension_validation(self, client):
        """测试文件扩展名验证"""
        invalid_extensions = [
            'malware.exe',
            'script.sh',
            'payload.php',
            'virus.bat'
        ]

        for filename in invalid_extensions:
            data = {
                'avatar': (io.BytesIO(b'malicious content'), filename),
                'user_id': 'attacker'
            }
            response = client.post('/api/avatar/upload', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 400
            assert json_data['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
