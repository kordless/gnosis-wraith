    // Simulates progress updates during the crawling operation with longer OCR processing time
    function simulateProgressDuringCrawl(statusTextElement, progressIndicator, options) {
        const { takeScreenshot, ocrExtraction, markdownExtraction } = options;
        
        // Define the crawling stages with expected percentages and messages
        const stages = [
            { percentage: 10, message: 'Starting browser...', durationMs: 1000 },
            { percentage: 15, message: 'Browser initialized', durationMs: 800 },
            { percentage: 20, message: 'Navigating to URL...', durationMs: 1200 },
            { percentage: 30, message: 'Retrieving page content...', durationMs: 1500 }
        ];
        
        // Add conditional stages based on options
        if (takeScreenshot) {
            stages.push({ percentage: 35, message: 'Taking screenshot...', durationMs: 1500 });
            
            if (ocrExtraction) {
                // OCR phase - make this take much longer to simulate the heavy processing
                stages.push({ percentage: 40, message: 'Preparing OCR analysis...', durationMs: 2000 });
                stages.push({ percentage: 45, message: 'OCR processing in progress...', durationMs: 3000 });
                stages.push({ percentage: 50, message: 'OCR analysis continuing...', durationMs: 4000 });
                stages.push({ percentage: 55, message: 'Extracting text from image...', durationMs: 5000 });
                // Hold at 60% for a long time during OCR
                stages.push({ percentage: 60, message: 'OCR text extraction (this may take a while)...', durationMs: 10000 });
            }
        }
        
        if (markdownExtraction !== 'none') {
            stages.push({ percentage: 75, message: 'Generating markdown content...', durationMs: 1500 });
            
            if (markdownExtraction === 'enhanced') {
                stages.push({ percentage: 80, message: 'Applying content filtering...', durationMs: 1200 });
            }
        }
        
        // Final stages - these will progress more quickly once the server starts responding
        stages.push({ percentage: 85, message: 'Creating report...', durationMs: 1000 });
        stages.push({ percentage: 90, message: 'Finalizing...', durationMs: 800 });
        
        let currentStageIndex = 0;
        
        // Update immediately with the first stage
        updateProgress(statusTextElement, progressIndicator, stages[0].message, stages[0].percentage);
        
        // Set up interval to process the stages with dynamic timing
        let timerId = null;
        const processNextStage = () => {
            currentStageIndex++;
            
            // If we've gone through all stages, just keep showing the last one
            if (currentStageIndex >= stages.length) {
                // Hold at the last stage
                return;
            }
            
            // Update with the current stage
            const currentStage = stages[currentStageIndex];
            updateProgress(statusTextElement, progressIndicator, currentStage.message, currentStage.percentage);
            
            // Schedule the next stage
            timerId = setTimeout(processNextStage, currentStage.durationMs);
        };
        
        // Start the first timeout
        timerId = setTimeout(processNextStage, stages[0].durationMs);
        
        // Return a function that can clear the timer
        return () => {
            if (timerId) {
                clearTimeout(timerId);
                timerId = null;
            }
        };
    }