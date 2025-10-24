def get_playlist_videos(youtube, playlist_id):
    videos = []
    next_page_token = None
    while True:
        pl_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        pl_response = pl_request.execute()
        for item in pl_response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]
            videos.append({"id": video_id, "title": title})
        next_page_token = pl_response.get("nextPageToken")
        if not next_page_token:
            break
    return videos


def filter_private_videos_batched(youtube, videos):
    private_videos = []
    ids = [v["id"] for v in videos]
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        req = youtube.videos().list(part="status", id=",".join(chunk))
        resp = req.execute()
        privacy_by_id = {item["id"]: item["status"].get("privacyStatus") for item in resp.get("items", [])}
        for v in videos[i:i+50]:
            status = privacy_by_id.get(v["id"])
            if status == "private":
                v["privacyStatus"] = status
                private_videos.append(v)
    return private_videos
