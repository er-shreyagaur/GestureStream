// GestureStream application script

// Store current active video and control variables
let activeVideoPlayer = null;
const videoPlayers = [];
let gestureControlActive = false;
let commandInterval = null;
let lastCommandTime = 0;
const commandCooldown = 1000; // 1 second cooldown between commands

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", function () {
  // Get all video players
  const players = document.querySelectorAll("video");
  players.forEach((player, index) => {
    videoPlayers.push(player);

    // Add click handler to make a video active
    player.addEventListener("click", () => {
      setActiveVideo(player);
    });
  });

  // Set the first video as active by default
  if (videoPlayers.length > 0) {
    setActiveVideo(videoPlayers[0]);
  }

  // Initialize button event listeners
  const startBtn = document.getElementById("startGestureBtn");
  const stopBtn = document.getElementById("stopGestureBtn");
  const statusIndicator = document.getElementById("gestureStatusIndicator");

  updateStatusIndicator(false);

  startBtn.addEventListener("click", startGestureControl);
  stopBtn.addEventListener("click", stopGestureControl);

  // Add event listeners for mode buttons
  document
    .getElementById("gestureMode")
    .addEventListener("click", () => setMode("gesture"));
  document
    .getElementById("voiceMode")
    .addEventListener("click", () => setMode("voice"));
  document
    .getElementById("bothMode")
    .addEventListener("click", () => setMode("both"));

  // Add keyboard shortcuts for testing
  document.addEventListener("keydown", (e) => {
    if (!gestureControlActive) return;

    switch (e.key) {
      case " ":
        executeCommand("play_pause");
        break;
      case "ArrowUp":
        executeCommand("volume_up");
        break;
      case "ArrowDown":
        executeCommand("volume_down");
        break;
      case "ArrowRight":
        executeCommand("skip_forward");
        break;
      case "ArrowLeft":
        executeCommand("skip_backward");
        break;
      case "n":
        executeCommand("next_video");
        break;
      case "p":
        executeCommand("previous_video");
        break;
    }
  });
});

// Set mode function
function setMode(mode) {
  fetch("/set_mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: mode }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data.status);
      // Update UI to show active mode
      document
        .querySelectorAll(".mode-button")
        .forEach((btn) => btn.classList.remove("active"));
      document.getElementById(mode + "Mode").classList.add("active");
      showNotification(`Switched to ${mode} mode`);
    })
    .catch((error) => console.error("Error setting mode:", error));
}

// Show instructions function
function showInstructions(type) {
  // Hide all instruction content
  document.querySelectorAll(".instruction-content").forEach((content) => {
    content.classList.remove("active");
  });

  // Show selected content
  document.getElementById(type + "Instructions").classList.add("active");

  // Update tab buttons
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.remove("active");
  });

  // Find the clicked button and make it active
  event.currentTarget.classList.add("active");
}

// Update status indicator
function updateStatusIndicator(active) {
  const indicator = document.getElementById("gestureStatusIndicator");
  if (indicator) {
    if (active) {
      indicator.classList.remove("status-inactive");
      indicator.classList.add("status-active");
      indicator.textContent = "System Status: Active";
    } else {
      indicator.classList.remove("status-active");
      indicator.classList.add("status-inactive");
      indicator.textContent = "System Status: Inactive";
    }
  }
}

// Set active video function
function setActiveVideo(player) {
  // Remove active class from all videos
  videoPlayers.forEach((p) => p.classList.remove("active-video"));

  // Add active class to selected video
  player.classList.add("active-video");
  activeVideoPlayer = player;

  // Show visual feedback
  showCommandFeedback("Video Selected", player);

  console.log(
    "Active video set:",
    player.querySelector("source")?.getAttribute("src") || "unknown source"
  );
}

// Switch to next or previous video
function switchVideo(direction) {
  if (videoPlayers.length <= 1) return;

  const currentIndex = videoPlayers.indexOf(activeVideoPlayer);
  let newIndex;

  if (direction === "next") {
    newIndex = (currentIndex + 1) % videoPlayers.length;
  } else {
    newIndex = (currentIndex - 1 + videoPlayers.length) % videoPlayers.length;
  }

  setActiveVideo(videoPlayers[newIndex]);
}

// Start gesture control
function startGestureControl() {
  fetch("/start_gesture", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log(data.status);
      gestureControlActive = true;
      updateStatusIndicator(true);
      showNotification(data.status || "Gesture control started");

      // Enable/disable buttons
      document.getElementById("startGestureBtn").disabled = true;
      document.getElementById("stopGestureBtn").disabled = false;

      // Start polling for commands
      if (commandInterval === null) {
        commandInterval = setInterval(pollCommands, 300);
      }
    })
    .catch((error) => {
      console.error("Error starting gesture control:", error);
      showNotification("Failed to start gesture control", true);
    });
}

// Stop gesture control
function stopGestureControl() {
  fetch("/stop_gesture", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log(data.status);
      gestureControlActive = false;
      updateStatusIndicator(false);
      showNotification(data.status || "Gesture control stopped");

      // Enable/disable buttons
      document.getElementById("startGestureBtn").disabled = false;
      document.getElementById("stopGestureBtn").disabled = true;

      // Stop polling for commands
      if (commandInterval !== null) {
        clearInterval(commandInterval);
        commandInterval = null;
      }
    })
    .catch((error) => {
      console.error("Error stopping gesture control:", error);
      showNotification("Failed to stop gesture control", true);
    });
}

// Poll for commands from the server
function pollCommands() {
  fetch("/get_commands")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data.commands || data.commands.length === 0) {
        return;
      }

      const now = Date.now();
      if (now - lastCommandTime < commandCooldown) {
        // Don't process commands too quickly
        return;
      }

      // Process latest command only to avoid command queue buildup
      const latestCommand = data.commands[data.commands.length - 1];
      executeCommand(latestCommand);
      lastCommandTime = now;
    })
    .catch((error) => {
      console.error("Error polling commands:", error);
      // Don't show notification for polling errors to avoid spamming
    });
}

// Show notification
function showNotification(message, isError = false) {
  if (window.Notification && Notification.permission === "granted") {
    new Notification("GestureStream", { body: message });
  } else {
    const notification = document.createElement("div");
    notification.className = "notification " + (isError ? "error" : "success");
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.opacity = "0";
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 500);
    }, 3000);
  }
}

// Show command feedback
function showCommandFeedback(command, target = activeVideoPlayer) {
  if (!target) return;

  const feedback = document.createElement("div");
  feedback.className = "command-feedback";
  feedback.textContent = command;
  feedback.style.position = "absolute";
  feedback.style.color = "white";
  feedback.style.background = "rgba(0,0,0,0.7)";
  feedback.style.padding = "5px 10px";
  feedback.style.borderRadius = "4px";
  feedback.style.zIndex = "1000";
  feedback.style.opacity = "0";
  feedback.style.transition = "opacity 0.3s ease";

  // Position at center of video
  const rect = target.getBoundingClientRect();
  feedback.style.left = `${rect.left + rect.width / 2 - 50}px`;
  feedback.style.top = `${rect.top + rect.height / 2 - 15}px`;

  document.body.appendChild(feedback);

  // Animate
  setTimeout(() => {
    feedback.style.opacity = "1";
    setTimeout(() => {
      feedback.style.opacity = "0";
      setTimeout(() => {
        document.body.removeChild(feedback);
      }, 500);
    }, 1500);
  }, 10);
}

// Execute received command
function executeCommand(command) {
  // Make sure we have an active player
  if (
    !activeVideoPlayer &&
    command !== "next_video" &&
    command !== "previous_video"
  ) {
    console.warn("No active video player selected");
    return;
  }

  console.log("Executing command:", command);

  switch (command) {
    case "play_pause":
      if (activeVideoPlayer.paused) {
        activeVideoPlayer.play();
        showCommandFeedback("Play");
      } else {
        activeVideoPlayer.pause();
        showCommandFeedback("Pause");
      }
      break;

    case "volume_up":
      activeVideoPlayer.volume = Math.min(1, activeVideoPlayer.volume + 0.1);
      showCommandFeedback(
        `Volume: ${Math.round(activeVideoPlayer.volume * 100)}%`
      );
      break;

    case "volume_down":
      activeVideoPlayer.volume = Math.max(0, activeVideoPlayer.volume - 0.1);
      showCommandFeedback(
        `Volume: ${Math.round(activeVideoPlayer.volume * 100)}%`
      );
      break;

    case "skip_forward":
      activeVideoPlayer.currentTime += 10; // Skip forward 10 seconds
      showCommandFeedback("Forward 10s");
      break;

    case "skip_backward":
      activeVideoPlayer.currentTime -= 10; // Skip backward 10 seconds
      showCommandFeedback("Back 10s");
      break;

    case "next_video":
      switchVideo("next");
      showCommandFeedback("Next Video");
      break;

    case "previous_video":
      switchVideo("previous");
      showCommandFeedback("Previous Video");
      break;

    case "fullscreen":
      if (!document.fullscreenElement) {
        activeVideoPlayer.requestFullscreen().catch((err) => {
          console.error(
            `Error attempting to enable fullscreen: ${err.message}`
          );
        });
      } else {
        document.exitFullscreen();
      }
      showCommandFeedback("Fullscreen Toggle");
      break;

    default:
      console.warn("Unknown command:", command);
  }
}

// Add CSS for notifications and feedback
(function addStyles() {
  const style = document.createElement("style");
  style.textContent = `
    .notification {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      padding: 10px 20px;
      border-radius: 4px;
      color: white;
      z-index: 1000;
      opacity: 1;
      transition: opacity 0.5s ease;
    }
    .notification.success {
      background-color: #4CAF50;
    }
    .notification.error {
      background-color: #F44336;
    }
    .active-video {
      border: 3px solid #4CAF50;
    }
    .command-feedback {
      pointer-events: none;
      font-weight: bold;
    }
  `;
  document.head.appendChild(style);
})();
