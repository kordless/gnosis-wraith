// Script for handling image uploads
document.addEventListener('DOMContentLoaded', function() {
  // Get all required elements
  const fileInput = document.getElementById('image-file-input');
  const fileSelectBtn = document.getElementById('file-select-btn');
  const fileSelectionText = document.getElementById('file-selection-text');
  const uploadBtn = document.getElementById('upload-btn');
  const selectedFileInfo = document.getElementById('selected-file-info');
  const selectedFilename = document.getElementById('selected-filename');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const searchBox = document.querySelector('.ghost-search-box');
  
  // Function to update the UI based on file selection
  function updateFileSelectionUI() {
    // Safety check in case fileInput is null
    if (!fileInput) {
      console.warn('File input element not found, skipping UI update');
      return;
    }
    
    if (fileInput.files && fileInput.files.length > 0) {
      // File is selected - update all UI elements
      const fileName = fileInput.files[0].name;
      
      // Update selection text
      fileSelectionText.textContent = `File selected: ${fileName}`;
      fileSelectionText.style.color = '#6c63ff';
      
      // Update file info area
      if (selectedFilename) selectedFilename.textContent = fileName;
      if (selectedFileInfo) selectedFileInfo.style.display = 'block';
      
      // Enable upload button
      uploadBtn.disabled = false;
      uploadBtn.style.opacity = '1';
      uploadBtn.style.cursor = 'pointer';
    } else {
      // No file selected - reset UI
      fileSelectionText.textContent = 'Select image or drop file here...';
      fileSelectionText.style.color = '#999';
      
      // Hide file info
      if (selectedFileInfo) selectedFileInfo.style.display = 'none';
      
      // Disable upload button
      uploadBtn.disabled = true;
      uploadBtn.style.opacity = '0.6';
      uploadBtn.style.cursor = 'not-allowed';
    }
  }
  
  // Make the entire search box clickable to select a file
  if (searchBox) {
    searchBox.addEventListener('click', function(e) {
      // Check if all required elements exist
      if (!fileInput) {
        console.warn('File input element not found, skipping click handler');
        return;
      }
      
      if (!fileSelectBtn) {
        console.warn('File select button not found, using simpler click handler');
        fileInput.click();
        return;
      }
      
      // Only trigger if not clicking on the folder button or the remove button
      if (e.target !== fileSelectBtn && 
          !fileSelectBtn.contains(e.target) && 
          (removeFileBtn === null || (e.target !== removeFileBtn && 
          !removeFileBtn?.contains(e.target)))) {
        fileInput.click();
      }
    });
  }
  
  // Make the file select button work
  if (fileSelectBtn) {
    fileSelectBtn.addEventListener('click', function(e) {
      e.preventDefault();
      fileInput.click();
    });
  }
  
  // Update UI when a file is selected
  if (fileInput) {
    fileInput.addEventListener('change', updateFileSelectionUI);
  }
  
  // Handle remove button
  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      fileInput.value = '';
      updateFileSelectionUI();
    });
  }
  
  // Get OCR setting for form submission
  function getOcrEnabled() {
    const ocrToggle = document.getElementById('ocr-extraction-toggle');
    return ocrToggle && ocrToggle.checked ? 'true' : 'false';
  }
  
  // Handle file upload when the upload button is clicked
  if (uploadBtn) {
    uploadBtn.addEventListener('click', async function(e) {
      e.preventDefault();
      
      if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select an image to upload');
        return;
      }
      
      // Get custom title if specified
      const titleToggle = document.getElementById('upload-report-title-toggle');
      const titleInput = document.getElementById('upload-report-title');
      let title = 'Image Analysis Report';
      
      if (titleToggle && titleToggle.checked && titleInput && titleInput.value) {
        title = titleInput.value;
      }
      
      // Create FormData
      const formData = new FormData();
      formData.append('image', fileInput.files[0]);
      formData.append('title', title);
      formData.append('ocr_extraction', getOcrEnabled());
      
      console.log('Uploading with title:', title, 'OCR enabled:', getOcrEnabled());
      
      // Show status indicator
      const statusBox = document.getElementById('upload-status');
      const statusText = document.getElementById('upload-status-text');
      const progressIndicator = document.getElementById('upload-progress-indicator');
      
      if (statusBox && statusText && progressIndicator) {
        statusBox.style.display = 'block';
        statusText.textContent = 'Uploading image...';
        progressIndicator.style.width = '30%';
      }
      
      try {
        // Send to server
        const response = await fetch(window.location.origin + '/api/upload', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error('Server returned error status: ' + response.status);
        }
        
        const result = await response.json();
        console.log('Upload successful:', result);
        
        // Update progress to complete
        if (statusText && progressIndicator) {
          statusText.textContent = 'Upload complete!';
          progressIndicator.style.width = '100%';
        }
        
        // Display result (if needed)
        if (typeof displayResult === 'function') {
          displayResult(result);
        }
        
        // Hide status after a moment
        setTimeout(() => {
          if (statusBox) statusBox.style.display = 'none';
        }, 2000);
        
      } catch (error) {
        console.error('Upload failed:', error);
        
        // Show error
        if (statusText && progressIndicator) {
          statusText.textContent = 'Error: ' + error.message;
          progressIndicator.style.width = '100%';
          progressIndicator.style.backgroundColor = '#e74c3c';
        }
        
        alert('Upload failed: ' + error.message);
      }
    });
  }
  
  // Setup drag and drop
  if (searchBox) {
    // Prevent default behaviors for all drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      searchBox.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });
    
    // Highlight the drop area when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
      searchBox.addEventListener(eventName, function() {
        searchBox.classList.add('highlight');
      }, false);
    });
    
    // Remove highlight when leaving or after drop
    ['dragleave', 'drop'].forEach(eventName => {
      searchBox.addEventListener(eventName, function() {
        searchBox.classList.remove('highlight');
      }, false);
    });
    
    // Handle the actual drop
    searchBox.addEventListener('drop', function(e) {
      const droppedFiles = e.dataTransfer.files;
      
      if (droppedFiles.length > 0) {
        // Set the file input's files to the dropped file
        fileInput.files = droppedFiles;
        
        // Update the UI
        updateFileSelectionUI();
      }
    }, false);
  }
  
  // Initialize the UI state
  updateFileSelectionUI();
});