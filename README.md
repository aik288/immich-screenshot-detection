# Immich Screenshot Categorizer

A dockerized application that automatically identifies and categorizes screenshots in your Immich photo library using advanced computer vision techniques.

## Features

-   **Automatic Screenshot Detection**: Uses multiple computer vision algorithms to identify screenshots
-   **Immich Integration**: Seamlessly integrates with your existing Immich installation
-   **Smart Tagging**: Automatically tags detected screenshots with customizable tags
-   **Album Creation**: Optionally creates albums for organizing screenshots
-   **Batch Processing**: Efficiently processes photos in configurable batches
-   **Docker Support**: Fully containerized for easy deployment alongside Immich

## Detection Methods

The application uses several sophisticated techniques to identify screenshots:

1. **Edge Detection**: Analyzes UI elements and interface patterns
2. **Color Analysis**: Examines color distribution typical of screenshots
3. **Text Detection**: Identifies text regions common in screenshots
4. **Geometric Patterns**: Detects rectangular shapes and buttons
5. **Aspect Ratio Analysis**: Checks for common screen dimensions
6. **Metadata Analysis**: Examines EXIF data for screenshot indicators

## Quick Start

### Prerequisites

-   Docker and Docker Compose installed
-   Running Immich instance
-   Immich API key and User ID

### 1. Get Your Immich API Key

1. Log into your Immich web interface
2. Go to Account Settings → API Keys
3. Create a new API key
4. Copy the API key for configuration

### 2. (Optional) Get Your User ID

The API key already identifies the user, so `IMMICH_USER_ID` is optional. If you want it, you can read it from the API:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://your-immich-server:2283/api/users/me
```

### 3. Configuration

1. Copy the example configuration:

    ```bash
    cp config.env.example .env
    ```

2. Edit `.env` with your settings:

    ```env
    # Required settings
    IMMICH_API_KEY=your-immich-api-key-here
    IMMICH_SERVER_URL=http://your-immich-server:2283

    # Optional settings
    IMMICH_USER_ID=your-user-id-here
    SCREENSHOT_CONFIDENCE_THRESHOLD=0.7
    BATCH_SIZE=10
    SCREENSHOT_TAG=screenshot
    CREATE_ALBUM=true
    ALBUM_NAME=Screenshots
    ```

### 4. Running with Docker Compose

The included `docker-compose.yml` runs only the categorizer and expects an existing Immich stack on an external Docker network.

1. Find the network used by your Immich containers:

    ```bash
    docker network ls
    ```

2. Set `IMMICH_NETWORK` in `.env` (for example `immich_default`).

3. Build and run the one-shot job:

    ```bash
    docker compose up --build
    ```

The container exits when the scan finishes.

#### Adding to an existing Immich compose file

Add this service to the compose file that already runs Immich, using the same network:

```yaml
services:
    immich-screenshot-categorizer:
        build: .
        container_name: immich-screenshot-categorizer
        restart: "no"
        networks:
            - immich
        env_file:
            - .env
        environment:
            IMMICH_SERVER_URL: http://immich-server:2283
        volumes:
            - ./logs:/app/logs
```

### 5. Running as One-Shot Container

If you prefer to run the categorizer without Compose:

```bash
docker build -t immich-screenshot-categorizer .

docker run --rm \
  --env-file .env \
  --network immich_default \
  -v "$(pwd)/logs:/app/logs" \
  immich-screenshot-categorizer
```

## Configuration Options

| Variable                          | Default                 | Description                                             |
| --------------------------------- | ----------------------- | ------------------------------------------------------- |
| `IMMICH_API_KEY`                  | _required_              | Your Immich API key                                     |
| `IMMICH_USER_ID`                  | _optional_              | Your Immich user ID (the API key already identifies you) |
| `IMMICH_SERVER_URL`               | `http://localhost:2283` | Immich server URL (the client appends `/api`)           |
| `SCREENSHOT_CONFIDENCE_THRESHOLD` | `0.7`                   | Confidence threshold for screenshot detection (0.0-1.0) |
| `BATCH_SIZE`                      | `10`                    | Number of photos to process in each batch               |
| `MAX_IMAGE_SIZE`                  | `2048`                  | Maximum image size for processing (pixels)              |
| `LOG_LEVEL`                       | `INFO`                  | Logging level (DEBUG, INFO, WARNING, ERROR)             |
| `SCREENSHOT_TAG`                  | `screenshot`            | Tag to apply to detected screenshots                    |
| `CREATE_ALBUM`                    | `true`                  | Whether to create an album for screenshots              |
| `ALBUM_NAME`                      | `Screenshots`           | Name of the screenshot album                            |

## Monitoring

### Logs

View logs in real-time:

```bash
docker compose logs -f immich-screenshot-categorizer
```

### Job Status

This is a one-shot batch job, so it does not expose a long-running health check. Inspect the exit code and logs:

```bash
docker compose ps
docker compose logs immich-screenshot-categorizer
```

## Troubleshooting

### Common Issues

1. **API Key Issues**

    - Ensure your API key is valid and has the necessary permissions
    - Check that the API key hasn't expired

2. **Network Connectivity**

    - Verify that the categorizer can reach your Immich server
    - Check Docker network configuration

3. **Permission Errors**

    - Ensure the API key has read/write permissions for assets and tags
    - Check that the API key belongs to the user that owns the assets

4. **High Memory Usage**
    - Reduce `BATCH_SIZE` for lower memory usage
    - Reduce `MAX_IMAGE_SIZE` to limit memory per image

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG docker compose up --build
```

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│  Immich Server      │    │  Screenshot         │
│  ┌─────────────────┐│    │  Categorizer        │
│  │   API           ││◄──►│  ┌─────────────────┐│
│  │   /api/assets   ││    │  │ Immich Client   ││
│  │   /api/albums   ││    │  │                 ││
│  └─────────────────┘│    │  └─────────────────┘│
│                     │    │  ┌─────────────────┐│
│  ┌─────────────────┐│    │  │ Screenshot      ││
│  │   Photo         ││    │  │ Detector        ││
│  │   Storage       ││    │  │ - Edge Analysis ││
│  └─────────────────┘│    │  │ - Color Hist.   ││
└─────────────────────┘    │  │ - Text Detection││
                           │  │ - Geometric     ││
                           │  │ - Metadata      ││
                           │  └─────────────────┘│
                           └─────────────────────┘
```

## Performance

-   **Processing Speed**: ~1-5 photos per second (depends on image size and complexity)
-   **Memory Usage**: ~100-500MB (depends on batch size and image size)
-   **CPU Usage**: Moderate (computer vision operations are CPU-intensive)

## Security Considerations

-   API keys are sensitive - use environment variables or Docker secrets
-   The application runs as a non-root user inside the container
-   Network access is limited to the Immich API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the logs for error messages
3. Open an issue on GitHub with:
    - Your configuration (remove sensitive data)
    - Log output
    - Steps to reproduce the issue

## Roadmap

-   [ ] Machine learning-based detection improvements
-   [ ] Support for video screenshot detection
-   [ ] Integration with other photo management systems
-   [ ] Web UI for configuration and monitoring
-   [ ] Support for custom detection rules
