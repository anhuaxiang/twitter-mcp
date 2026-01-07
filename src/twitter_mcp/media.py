import os
import requests
from typing import Optional, Tuple
import mimetypes


class MediaManager:
    """Twitter媒体上传管理器，支持分块上传"""

    # Twitter API支持的媒体类型对应的category
    MEDIA_CATEGORIES = {
        'image/jpeg': 'tweet_image',
        'image/png': 'tweet_image',
        'image/gif': 'tweet_gif',
        'video/mp4': 'tweet_video',
        'video/quicktime': 'tweet_video',
    }

    # 默认分块大小（字节），Twitter建议每个块不超过1MB
    DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB

    def __init__(self, bearer_token: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        初始化MediaManager

        Args:
            bearer_token: Twitter API的Bearer Token
            chunk_size: 分块上传时每块的大小（字节），默认1MB
        """
        self.bearer_token = bearer_token
        self.chunk_size = chunk_size
        self.headers = {
            'Authorization': f'Bearer {bearer_token}'
        }

    def _infer_media_category(self, media_type: str) -> str:
        """
        根据媒体类型推断media_category

        Args:
            media_type: MIME类型，如'image/jpeg'

        Returns:
            对应的media_category，如果未知则返回'tweet_image'
        """
        return self.MEDIA_CATEGORIES.get(media_type, 'tweet_image')

    def _get_media_type(self, file_path: str) -> Tuple[str, str]:
        """
        获取文件的MIME类型

        Args:
            file_path: 文件路径

        Returns:
            (media_type, media_category)元组
        """
        media_type, _ = mimetypes.guess_type(file_path)

        if not media_type:
            # 如果无法推断，使用默认类型
            media_type = 'application/octet-stream'

        media_category = self._infer_media_category(media_type)

        return media_type, media_category

    def upload_media(self, file_path: str) -> str:
        """
        上传媒体文件到Twitter，支持分块上传

        Args:
            file_path: 要上传的文件路径

        Returns:
            media_id_string: 上传成功后的媒体ID字符串

        Raises:
            Exception: 上传失败时抛出异常
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = os.path.getsize(file_path)
        media_type, media_category = self._get_media_type(file_path)

        # 步骤1: 初始化上传
        media_id = self._initialize_upload(media_type, file_size, media_category)

        # 步骤2: 分块上传文件内容
        self._upload_chunks(file_path, media_id)

        # 步骤3: 完成上传
        self._finalize_upload(media_id)

        return media_id

    def _initialize_upload(self, media_type: str, file_size: int, media_category: str) -> str:
        """
        初始化媒体上传

        Args:
            media_type: MIME类型
            file_size: 文件大小（字节）
            media_category: 媒体分类

        Returns:
            media_id: 媒体ID
        """
        init_data = {
            "media_type": media_type,
            "total_bytes": file_size,
            "media_category": media_category
        }

        response = requests.post(
            "https://api.twitter.com/2/media/upload/initialize",
            headers=self.headers,
            json=init_data
        )

        if response.status_code != 200:
            raise Exception(f"初始化上传失败: {response.status_code}, {response.text}")

        media_id = response.json().get('data', {}).get('id')
        if not media_id:
            raise Exception("未能获取media_id")

        return media_id

    def _upload_chunks(self, file_path: str, media_id: str):
        """
        分块上传文件内容

        Args:
            file_path: 文件路径
            media_id: 媒体ID
        """
        with open(file_path, 'rb') as f:
            segment_index = 0

            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break

                self._append_chunk(media_id, segment_index, chunk)
                segment_index += 1

    def _append_chunk(self, media_id: str, segment_index: int, chunk_data: bytes):
        """
        追加一个数据块

        Args:
            media_id: 媒体ID
            segment_index: 块索引
            chunk_data: 块数据
        """
        files = {
            "media": ("blob", chunk_data, "application/octet-stream")
        }

        data = {
            "segment_index": str(segment_index)
        }

        response = requests.post(
            f"https://api.twitter.com/2/media/upload/{media_id}/append",
            headers=self.headers,
            data=data,
            files=files
        )

        if response.status_code != 200:
            raise Exception(f"上传块{segment_index}失败: {response.status_code}, {response.text}")

    def _finalize_upload(self, media_id: str):
        """
        完成上传

        Args:
            media_id: 媒体ID
        """
        response = requests.post(
            f"https://api.twitter.com/2/media/upload/{media_id}/finalize",
            headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(f"完成上传失败: {response.status_code}, {response.text}")

    def upload_media_from_bytes(self, media_data: bytes, media_type: str, filename: str = "media") -> str:
        """
        从字节数据上传媒体（用于从URL下载的媒体）

        Args:
            media_data: 媒体字节数据
            media_type: MIME类型
            filename: 文件名（用于推断类型，可选）

        Returns:
            media_id_string: 上传成功后的媒体ID字符串
        """
        file_size = len(media_data)
        media_category = self._infer_media_category(media_type)

        # 初始化上传
        media_id = self._initialize_upload(media_type, file_size, media_category)

        # 分块上传
        self._upload_bytes(media_data, media_id)

        # 完成上传
        self._finalize_upload(media_id)

        return media_id

    def _upload_bytes(self, data: bytes, media_id: str):
        """
        分块上传字节数据

        Args:
            data: 字节数据
            media_id: 媒体ID
        """
        total_size = len(data)
        segment_index = 0
        offset = 0

        while offset < total_size:
            chunk = data[offset:offset + self.chunk_size]
            self._append_chunk(media_id, segment_index, chunk)
            offset += self.chunk_size
            segment_index += 1