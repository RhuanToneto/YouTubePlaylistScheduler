def get_playlist_videos(youtube, playlist_id):
    # Lê vídeos da playlist em páginas de 50 até esgotar os itens.
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
    # Filtra vídeos privados consultando em blocos de 50 IDs.
    private_videos = []
    ids = [v["id"] for v in videos]
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        req = youtube.videos().list(part="snippet,status", id=",".join(chunk))
        resp = req.execute()
        details_by_id = {item["id"]: item for item in resp.get("items", [])}
        for v in videos[i:i+50]:
            detail = details_by_id.get(v["id"])
            if not detail:
                continue
            status = detail.get("status", {}).get("privacyStatus")
            if status == "private":
                title = detail.get("snippet", {}).get("title")
                if title:
                    v["title"] = title
                v["privacyStatus"] = status
                private_videos.append(v)
    return private_videos
