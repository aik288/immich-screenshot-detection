#!/usr/bin/env python3
import os
from immich_client import Configuration, ApiClient
from immich_client.api import authentication_api, assets_api, albums_api


def main():
    # Configure API client
    config = Configuration(
        host="http://localhost:2283/api",  # Replace with your Immich server URL
        api_key={
            "api_key": os.getenv("IMMICH_API_KEY")
        },  # Set your API key in environment
    )

    # Create API client instance
    with ApiClient(config) as api_client:
        # Initialize API endpoints
        auth_api = authentication_api.AuthenticationApi(api_client)
        assets_api = assets_api.AssetsApi(api_client)
        albums_api = albums_api.AlbumsApi(api_client)

        try:
            # Example: Get server status
            status = auth_api.get_auth_status()
            print("Server status:", status)

            # Example: Get all assets
            assets = assets_api.get_all_assets()
            print(f"Found {len(assets)} assets")

            # Example: Get all albums
            albums = albums_api.get_all_albums()
            print(f"Found {len(albums)} albums")

        except Exception as e:
            print(f"Error accessing API: {e}")


if __name__ == "__main__":
    main()
