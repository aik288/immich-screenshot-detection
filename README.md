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

### 2. Get Your User ID

You can find your User ID in the Immich web interface URL or by using the API:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://your-immich-server:3001/api/users/me
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
    IMMICH_USER_ID=your-user-id-here
    IMMICH_SERVER_URL=http://your-immich-server:3001

    # Optional settings
    SCREENSHOT_CONFIDENCE_THRESHOLD=0.7
    BATCH_SIZE=10
    SCREENSHOT_TAG=screenshot
    CREATE_ALBUM=true
    ALBUM_NAME=Screenshots
    ```

### 4. Running with Docker Compose

#### Option A: Add to Existing Immich Setup

Add this service to your existing Immich docker-compose.yml:

```yaml
services:
    immich-screenshot-categorizer:
        build: https://github.com/your-repo/immich-screenshot-categorizer.git
        container_name: immich-screenshot-categorizer
        restart: unless-stopped
        depends_on:
            - immich-server
        networks:
            - immich-network
        environment:
            IMMICH_SERVER_URL: http://immich-server:3001
            IMMICH_API_KEY: ${IMMICH_API_KEY}
            IMMICH_USER_ID: ${IMMICH_USER_ID}
            SCREENSHOT_CONFIDENCE_THRESHOLD: ${SCREENSHOT_CONFIDENCE_THRESHOLD:-0.7}
            BATCH_SIZE: ${BATCH_SIZE:-10}
            SCREENSHOT_TAG: ${SCREENSHOT_TAG:-screenshot}
            CREATE_ALBUM: ${CREATE_ALBUM:-true}
            ALBUM_NAME: ${ALBUM_NAME:-Screenshots}
        volumes:
            - ./logs:/app/logs
```

#### Option B: Standalone with Full Immich Stack

```bash
# Clone the repository
git clone https://github.com/your-repo/immich-screenshot-categorizer.git
cd immich-screenshot-categorizer

# Configure environment
cp config.env.example .env
# Edit .env with your settings

# Start the full stack
docker-compose up -d
```

### 5. Running as One-Shot Container

If you prefer to run the categorizer as a one-time job:

```bash
docker run --rm \
  -e IMMICH_API_KEY=your-api-key \
  -e IMMICH_USER_ID=your-user-id \
  -e IMMICH_SERVER_URL=http://your-immich-server:3001 \
  --network immich-network \
  immich-screenshot-categorizer
```

## Configuration Options

| Variable                          | Default                 | Description                                             |
| --------------------------------- | ----------------------- | ------------------------------------------------------- |
| `IMMICH_API_KEY`                  | _required_              | Your Immich API key                                     |
| `IMMICH_USER_ID`                  | _required_              | Your Immich user ID                                     |
| `IMMICH_SERVER_URL`               | `http://localhost:3001` | Immich server URL                                       |
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
docker-compose logs -f immich-screenshot-categorizer
```

### Health Check

Check if the service is running:

```bash
docker-compose ps
```

The application includes health checks to ensure it's running properly.

## Troubleshooting

### Common Issues

1. **API Key Issues**

    - Ensure your API key is valid and has the necessary permissions
    - Check that the API key hasn't expired

2. **Network Connectivity**

    - Verify that the categorizer can reach your Immich server
    - Check Docker network configuration

3. **Permission Errors**

    - Ensure the API key has read/write permissions for assets
    - Check that the user ID is correct

4. **High Memory Usage**
    - Reduce `BATCH_SIZE` for lower memory usage
    - Reduce `MAX_IMAGE_SIZE` to limit memory per image

### Debug Mode

Enable debug logging:

```bash
docker-compose up -d -e LOG_LEVEL=DEBUG
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
