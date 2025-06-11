# Wraith File Upload Implementation Plan

## Overview
Add file upload capability to Wraith for processing local files, especially important for marine/edge computing use cases.

## Use Cases

### 1. Marine/Nautical Files
- **GPX/KML Routes**: Navigation routes and waypoints
- **GRIB Weather Files**: Binary weather data files
- **NMEA Logs**: Instrument data logs
- **Chart Updates**: S-57/S-63 electronic chart files

### 2. Business Documents
- **PDFs**: Extract text and analyze documents
- **Excel/CSV**: Process structured data
- **Images**: OCR extraction from screenshots/scans
- **Archives**: ZIP files with multiple documents

### 3. Technical Files
- **Log Files**: System/application logs for analysis
- **Config Files**: Parse and analyze configurations
- **Code Files**: Extract and analyze source code

## Implementation Approach

### Option 1: Add to Existing Wraith Interface (Recommended)
Add file upload alongside URL input in the main crawler interface.

```javascript
// Update crawler-input.js
const CrawlerInput = ({ ... }) => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadMode, setUploadMode] = useState(false);
  
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    
    // Upload files to server
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    setUploadedFiles(result.files);
    
    // Process uploaded files
    handleProcessFiles(result.files);
  };
  
  return (
    <div className="crawler-input">
      {/* Toggle between URL and File mode */}
      <div className="mode-selector">
        <button 
          className={`mode-btn ${!uploadMode ? 'active' : ''}`}
          onClick={() => setUploadMode(false)}
        >
          <i className="fas fa-globe"></i> URL
        </button>
        <button 
          className={`mode-btn ${uploadMode ? 'active' : ''}`}
          onClick={() => setUploadMode(true)}
        >
          <i className="fas fa-file-upload"></i> File
        </button>
      </div>
      
      {!uploadMode ? (
        /* Existing URL input */
        <input type="text" placeholder="Enter URL..." />
      ) : (
        /* File upload interface */
        <div className="file-upload-zone">
          <input
            type="file"
            multiple
            onChange={handleFileUpload}
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.jpg,.png,.gpx,.grib"
          />
          <div className="upload-instructions">
            Drag files here or click to upload
          </div>
        </div>
      )}
    </div>
  );
};
```

### Option 2: Repurpose Vault as File Manager
Transform the locked Vault interface into a file upload and management system.

```javascript
// Transform vault.html into file manager
const VaultInterface = () => {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  
  return (
    <div className="vault-file-manager">
      <h1>Wraith File Vault</h1>
      
      <div className="file-upload-section">
        <FileDropzone onFilesAdded={handleFilesAdded} />
      </div>
      
      <div className="file-list">
        {files.map(file => (
          <FileCard 
            key={file.id}
            file={file}
            onProcess={() => processFile(file)}
            onDelete={() => deleteFile(file.id)}
          />
        ))}
      </div>
    </div>
  );
};
```

## Backend API Changes

### 1. File Upload Endpoint
```python
# web/routes/api.py
@api_bp.route('/api/upload', methods=['POST'])
async def upload_files():
    files = await request.files
    uploaded = []
    
    for file in files.getlist('files'):
        # Save to temporary storage
        file_path = await save_uploaded_file(file)
        
        # Detect file type and prepare for processing
        file_info = {
            'id': generate_id(),
            'name': file.filename,
            'path': file_path,
            'type': detect_file_type(file),
            'size': file.content_length,
            'uploaded_at': datetime.now()
        }
        
        uploaded.append(file_info)
    
    return jsonify({'files': uploaded})

@api_bp.route('/api/process-file', methods=['POST'])
async def process_file():
    data = await request.json
    file_id = data.get('file_id')
    
    # Create processing job
    job = await job_runner.trigger_job({
        'type': 'file_process',
        'file_id': file_id,
        'operations': data.get('operations', ['extract_text', 'analyze'])
    })
    
    return jsonify({'job_id': job.id})
```

### 2. File Processing Pipeline
```python
# core/file_processor.py
class FileProcessor:
    async def process_file(self, file_path: str, file_type: str):
        """Process uploaded file based on type"""
        
        if file_type == 'pdf':
            return await self.process_pdf(file_path)
        elif file_type == 'image':
            return await self.process_image(file_path)
        elif file_type == 'gpx':
            return await self.process_gpx(file_path)
        elif file_type == 'grib':
            return await self.process_grib(file_path)
        # ... more file types
    
    async def process_pdf(self, file_path: str):
        # Extract text
        text = await extract_pdf_text(file_path)
        
        # Generate markdown
        markdown = await convert_to_markdown(text)
        
        # Run through same pipeline as web content
        return await analyze_content(markdown)
```

## Marine-Specific File Handlers

```python
# core/marine/file_handlers.py
class MarineFileHandler:
    async def process_gpx(self, file_path: str):
        """Process GPS route files"""
        gpx_data = parse_gpx(file_path)
        
        # Extract waypoints and routes
        waypoints = gpx_data.waypoints
        routes = gpx_data.routes
        
        # Generate navigation summary
        summary = await generate_route_summary(routes)
        
        # Create visual representation
        chart_image = await forge_api.create_route_chart(routes)
        
        return {
            'type': 'navigation_route',
            'waypoints': waypoints,
            'routes': routes,
            'summary': summary,
            'chart': chart_image
        }
    
    async def process_grib(self, file_path: str):
        """Process weather GRIB files"""
        grib_data = decode_grib(file_path)
        
        # Extract weather parameters
        wind = grib_data.get_parameter('wind')
        waves = grib_data.get_parameter('waves')
        pressure = grib_data.get_parameter('pressure')
        
        # Generate weather routing
        routing = await calculate_weather_routing(
            wind, waves, vessel_profile
        )
        
        return {
            'type': 'weather_data',
            'parameters': {
                'wind': wind,
                'waves': waves,
                'pressure': pressure
            },
            'routing': routing
        }
```

## UI Components

### 1. File Drop Zone
```javascript
const FileDropzone = ({ onFilesAdded }) => {
  const [isDragging, setIsDragging] = useState(false);
  
  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    onFilesAdded(files);
    setIsDragging(false);
  };
  
  return (
    <div 
      className={`dropzone ${isDragging ? 'dragging' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <i className="fas fa-cloud-upload-alt fa-3x"></i>
      <p>Drag files here or click to browse</p>
      <input
        type="file"
        multiple
        onChange={(e) => onFilesAdded(Array.from(e.target.files))}
      />
    </div>
  );
};
```

### 2. File Type Icons
```javascript
const getFileIcon = (fileType) => {
  const icons = {
    'pdf': 'fa-file-pdf text-red-500',
    'image': 'fa-file-image text-blue-500',
    'excel': 'fa-file-excel text-green-500',
    'gpx': 'fa-route text-purple-500',
    'grib': 'fa-wind text-cyan-500',
    'log': 'fa-file-alt text-gray-500'
  };
  
  return icons[fileType] || 'fa-file text-gray-400';
};
```

## Storage Integration

```python
# Use Alaya for file storage
class FileStorage:
    async def store_uploaded_file(self, file, user_id):
        # Store in user's upload directory
        path = f"users/{user_id}/uploads/{file.filename}"
        
        # Save with metadata
        await alaya.store({
            'path': path,
            'content': file.content,
            'metadata': {
                'original_name': file.filename,
                'content_type': file.content_type,
                'size': file.content_length,
                'uploaded_at': datetime.now()
            }
        })
        
        return path
```

## Next Steps

1. **Decision**: Choose between adding to Wraith main UI or repurposing Vault
2. **MVP Features**:
   - Basic file upload (PDF, images, text)
   - OCR for images
   - Text extraction for PDFs
   - Simple analysis pipeline
3. **Marine Features**:
   - GPX route processing
   - GRIB weather decoding
   - NMEA log parsing
4. **Integration**:
   - Connect to existing Wraith processing pipeline
   - Store results in same format as URL crawls
   - Generate same report types

This would make Wraith a universal ingestion engine - whether the content comes from a URL or a file upload, it gets processed through the same intelligent pipeline.