let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const host = window.location.hostname;

function startRecording() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      const options = { mimeType: "audio/webm" };
      mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorder.ondataavailable = handleDataAvailable;
      mediaRecorder.onstop = handleStop;
      mediaRecorder.start();
      audioChunks = [];
    })
    .catch((error) => {
      console.error("Error accessing the microphone: ", error);
    });
}

function stopRecording() {
  mediaRecorder.stop();
}

function handleDataAvailable(event) {
  audioChunks.push(event.data);
}

function handleStop() {
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const userID = getCurrentUserID();
  sendAudioToServer(audioBlob, userID);
}

function sendAudioToServer(audioBlob, userID) {
  let formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  formData.append("user_id", userID);
  showLoader();
  updateVisualizerStatus("processing", "Processing audio...");

  // Set up timeout warning
  const timeoutWarning = setTimeout(() => {
    const loaderContent = document.querySelector(".loader-content p");
    if (loaderContent) {
      loaderContent.textContent = "Still processing... This is normal for longer recordings. Please wait.";
    }
  }, 45000); // Show warning after 45 seconds

  // Use relative URL for same-origin requests
  fetch(`/process-audio`, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      clearTimeout(timeoutWarning);
      if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server response:", data);
      if (data.error) {
        throw new Error(data.error);
      }
      displayMidiLink(data.midi_url);
      showNotification("Audio processed successfully! MIDI file is ready.", "success");
    })
    .catch((error) => {
      clearTimeout(timeoutWarning);
      console.error("Error sending audio data to the server: ", error);
      showNotification("Error processing audio: " + error.message, "error");
      updateVisualizerStatus("ready", "Ready to record");
      showPlaceholder();
    })
    .finally(() => {
      clearTimeout(timeoutWarning);
      hideLoader();
    });
}

function getCurrentUserID(){
  return currentUserID;
}

function showLoader() {
  const loader = document.getElementById("loader");
  const loaderContent = loader.querySelector(".loader-content p");
  if (loaderContent) {
    loaderContent.textContent = "Processing your audio... This may take up to 2 minutes for longer recordings.";
  }
  loader.style.display = "flex";
}

function hideLoader() {
  document.getElementById("loader").style.display = "none";
}

function showNotification(message, type = "info") {
  const notification = document.getElementById("notification");
  const notificationText = document.getElementById("notification-text");
  
  if (notification && notificationText) {
    notificationText.textContent = message;
    notification.className = `notification-shown ${type}`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      notification.className = "notification-hidden";
    }, 5000);
  }
}

// Function to handle description button
function toggleDescription() {
  const modalBackground = document.getElementById("modal-background");
  if (
    modalBackground.style.display === "none" ||
    !modalBackground.style.display
  ) {
    modalBackground.style.display = "flex";
  } else {
    modalBackground.style.display = "none";
  }
}

function toggleRecording() {
  const recordButton = document.getElementById("recordButton");
  const recordIcon = document.getElementById("recordIcon");

  if (!isRecording) {
    startRecording();
    recordButton.title = "Stop Recording";
    recordIcon.textContent = "stop";
    recordButton.classList.add("recording");
    updateVisualizerStatus("recording", "Recording...");
    hidePlaceholder();
  } else {
    stopRecording();
    recordButton.title = "Start Recording";
    recordIcon.textContent = "fiber_manual_record";
    recordButton.classList.remove("recording");
    updateVisualizerStatus("processing", "Processing...");
  }

  isRecording = !isRecording;
}

// Enhanced visual feedback functions
function updateVisualizerStatus(status, text) {
  const statusIndicator = document.getElementById("statusIndicator");
  const statusText = document.getElementById("statusText");
  
  if (statusIndicator && statusText) {
    statusText.textContent = text;
    
    // Remove all status classes
    statusIndicator.classList.remove("recording", "processing", "ready");
    
    // Add appropriate class
    if (status === "recording") {
      statusIndicator.classList.add("recording");
    } else if (status === "processing") {
      statusIndicator.classList.add("processing");
    } else {
      statusIndicator.classList.add("ready");
    }
  }
}

function hidePlaceholder() {
  const placeholder = document.getElementById("visualizerPlaceholder");
  if (placeholder) {
    placeholder.classList.add("hidden");
  }
}

function showPlaceholder() {
  const placeholder = document.getElementById("visualizerPlaceholder");
  if (placeholder) {
    placeholder.classList.remove("hidden");
  }
}

function playMidi() {
  const player = document.querySelector("midi-player");
  if (player) {
    player.start();
  }
}

function stopMidi() {
  const player = document.querySelector("midi-player");
  if (player) {
    player.stop();
  }
}

function playPostMidi(playerId) {
  const player = document.getElementById(playerId);
  if (player) {
    player.start();
  }
}

function stopPostMidi(playerId) {
  const player = document.getElementById(playerId);
  if (player) {
    player.stop();
  }
}

function displayMidiLink(midiUrl) {
  // Update MIDI player and visualizer source
  if (!midiUrl) {
    console.error("midi url is undefined");
    return;
  }
  // console.log(midiUrl); 
  const midiPlayer = document.querySelector("midi-player");
  const midiVisualizer = document.getElementById("myVisualizer");

  if (midiPlayer && midiVisualizer) {
    midiPlayer.src = midiUrl;
    midiVisualizer.src = midiUrl;
    
    // Hide placeholder and show MIDI visualization
    hidePlaceholder();
    updateVisualizerStatus("ready", "MIDI Ready");
    
    // Add a small delay to ensure the visualizer loads properly
    setTimeout(() => {
      const pianoRollContent = document.querySelector('.piano-roll-content');
      if (pianoRollContent) {
        pianoRollContent.classList.add('loaded');
      }
    }, 500);
  }

  const saveButton = document.getElementById("save");
  if (saveButton) {
    saveButton.setAttribute("data-midi-url", midiUrl);
  }
}

function downloadMidi() {
  const saveButton = document.getElementById("save");
  const midiUrl = saveButton.getAttribute("data-midi-url");
  if (midiUrl) {
    // Create a temporary link element to trigger download
    const link = document.createElement('a');
    link.href = midiUrl;
    link.download = midiUrl.split('/').pop() || 'midi_file.mid';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function uploadMidi() {
  const midiPlayer = document.querySelector("midi-player");
  const midiSrc = midiPlayer ? midiPlayer.src : null;

  if (!midiSrc) {
    console.error("No MIDI source to upload");
    return;
  }

  // Extract filename from proxy URL
  const filename = midiSrc.split("/").pop();

  fetch(`/upload-midi`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename: filename }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error uploading MIDI file:", data.error);
        showNotification("Error uploading MIDI: " + data.error, "error");
      } else {
        console.log("MIDI file uploaded successfully:", data.message);
        showNotification("MIDI file uploaded successfully!", "success");
      }
    })
    .catch((error) => {
      console.error("Error in MIDI file upload:", error);
      showNotification("Error uploading MIDI file", "error");
    });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".midi-post").forEach((post) => {
    const midiPlayer = post.querySelector("midi-player");
    const midiVisualizer = post.querySelector("midi-visualizer");

    if (midiPlayer && midiVisualizer) {
      midiVisualizer.src = midiPlayer.src;
    }
  });
});

function downloadMidiPost(midiUrl) {
  if (midiUrl) {
    window.location.href = midiUrl; // This triggers the download
  }
}
