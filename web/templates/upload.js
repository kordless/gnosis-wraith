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
      // Only trigger if not clicking on the folder button or the remove button
      if (e.target !== fileSelectBtn && 
          !fileSelectBtn.contains(e.target) && 
          e.target !== removeFileBtn && 
          !removeFileBtn.contains(e.target)) {
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
