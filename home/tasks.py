import os
import shutil
from celery import shared_task


@shared_task
def delete_user_uploads(user_id):
    upload_path = os.path.join("media", "documents", str(user_id))

    try:
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path)
            return f"Deleted folder for user {user_id}"
        return f"No folder found for user {user_id}"
    except Exception as e:
        return str(e)