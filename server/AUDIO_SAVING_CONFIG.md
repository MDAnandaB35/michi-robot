# Audio File Saving Configuration

This document explains how to configure audio file saving behavior in the Michi Chatbot Server.

## Environment Variables

The server now supports two new environment variables to control audio file saving:

### `SAVE_WAKEWORD`

- **Values**: `"YES"` or `"NO"` (case-insensitive)
- **Default**: `"NO"`
- **Description**: Controls whether wakeword audio files are saved permanently or deleted after processing

### `SAVE_RESPONSES`

- **Values**: `"YES"` or `"NO"` (case-insensitive)
- **Default**: `"NO"`
- **Description**: Controls whether response audio files are saved permanently or deleted after streaming

## Configuration Examples

### Example 1: Save All Audio Files

```env
SAVE_WAKEWORD=YES
SAVE_RESPONSES=YES
```

### Example 2: Save Only Wakeword Audio

```env
SAVE_WAKEWORD=YES
SAVE_RESPONSES=NO
```

### Example 3: Save Only Response Audio

```env
SAVE_WAKEWORD=NO
SAVE_RESPONSES=YES
```

### Example 4: No Permanent Storage (Default)

```env
SAVE_WAKEWORD=NO
SAVE_RESPONSES=NO
```

## How It Works

### Wakeword Audio (`SAVE_WAKEWORD`)

- **When `YES`**: Audio is saved permanently as `wakeword_{timestamp}.wav` in the `wakeword_audio/` folder
- **When `NO`**: Audio is saved temporarily and automatically deleted after transcription

### Response Audio (`SAVE_RESPONSES`)

- **When `YES`**: Audio is saved permanently as `response_{timestamp}.mp3` in the `uploads/` folder
- **When `NO`**: Audio is saved temporarily and automatically deleted after streaming to the client

## API Endpoints

### List Wakeword Audio Files

```
GET /api/wakeword-audio
```

Returns list of all saved wakeword audio files (only works when `SAVE_WAKEWORD=YES`)

### List Response Audio Files

```
GET /api/response-audio
```

Returns list of all saved response audio files (only works when `SAVE_RESPONSES=YES`)

## File Management

### Automatic Cleanup

- Temporary files are automatically deleted after use
- Permanent files are never automatically deleted
- You can manually delete files from the respective folders

### Folder Structure

```
server/
├── wakeword_audio/          # Wakeword audio files (if SAVE_WAKEWORD=YES)
│   ├── wakeword_1703123456.wav
│   └── wakeword_1703123457.wav
├── uploads/                 # Response audio files (if SAVE_RESPONSES=YES)
│   ├── response_1703123456.mp3
│   └── response_1703123457.mp3
└── ...
```

## Benefits

### When Saving is Enabled (`YES`)

- **Debugging**: Review audio quality and transcription accuracy
- **Training**: Use saved files for improving wake word detection
- **Analysis**: Analyze user interaction patterns
- **Backup**: Keep historical audio data

### When Saving is Disabled (`NO`)

- **Storage Efficiency**: No disk space accumulation
- **Privacy**: Audio data is not permanently stored
- **Performance**: Faster processing without file I/O overhead
- **Compliance**: Meets data retention requirements

## Server Startup Information

When the server starts, it will display the current configuration:

```
🚀 Starting Michi Chatbot Server on port 5000
🔒 HTTPS is handled by AWS load balancer/reverse proxy
📁 Wakeword audio saving: ENABLED/DISABLED
📁 Response audio saving: ENABLED/DISABLED
📂 Wakeword folder: wakeword_audio
📂 Uploads folder: uploads
```

## Recommendations

- **Development/Testing**: Use `SAVE_WAKEWORD=YES` and `SAVE_RESPONSES=YES` for debugging
- **Production**: Use `SAVE_WAKEWORD=NO` and `SAVE_RESPONSES=NO` for privacy and storage efficiency
- **Hybrid**: Use `SAVE_WAKEWORD=YES` and `SAVE_RESPONSES=NO` to keep wakeword data for training while avoiding response storage
