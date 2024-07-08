const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const chatArea = document.querySelector(".chat-area");

const inactiveMessage = "Server is down, Please contact the developer to activate it";
var host = "http://127.0.0.1:5005/chat"; // Update the port and route according to your Flask app configuration
let passwordInput = false;

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    sendButton.click();
  }
});

function userResponseBtn(e) {
  send(e.value);
}

function send(message) {
  messageInput.type = "text"
  passwordInput = false;
  messageInput.focus();
  console.log("User Message:", message)

  // Disable the input field while the AJAX request is in progress
  messageInput.disabled = true;

  $.ajax({
      url: host,
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
          "message": message,
          "sender": "User"
      }),
      success: function(data, textStatus) {
        if (data != null) {
            setBotResponse(data);
        }
        console.log("Flask Response: ", data, "\n Status:", textStatus)

        // Enable the input field after the AJAX request has completed
        messageInput.disabled = false;
      },
      error: function(errorMessage) {
        setBotResponse("");
        console.log('Error' + errorMessage);

        // Enable the input field after the AJAX request has completed
        messageInput.disabled = false;

      }
  });
}

function createChatBubble(message, sender) {
  const bubble = document.createElement("div");
  bubble.classList.add("chat-bubble", sender + "-bubble");
  bubble.textContent = message;
  return bubble;
}

function setBotResponse(val) {
  setTimeout(function() {
      if (val.length < 1) {
          // If there is no response from Rasa
          const msg = inactiveMessage;
          chatArea.appendChild(createChatBubble(msg, 'bot'));
      } else {
        // If we get response from Rasa
        const botMsg = val;
        if (botMsg.includes("password")) {
            messageInput.type = "password";
            passwordInput = true;
        }
        chatArea.appendChild(createChatBubble(botMsg, 'bot'));
        }
    }, 1000);
}

function displaythumbnail(file){
  //This is to display the uploaded file thumbnail
  const fileType = file.type.split("/")[0];
  let thumbnail;
  if (fileType === "image") {
    thumbnail = document.createElement("img");
    thumbnail.src = URL.createObjectURL(file);
    thumbnail.alt = file.name;
  } else {
    thumbnail = document.createElement("i");
    thumbnail.classList.add("fas", "fa-file-alt");
  }

  const thumbnailBubble = document.createElement("div");
  thumbnailBubble.classList.add("chat-bubble", "bot-bubble", "file-bubble");
  thumbnailBubble.appendChild(thumbnail);

  // Appending the bot bubble to the chat area
  setTimeout(() => {
    chatArea.appendChild(thumbnailBubble);
  }, 500);
}


sendButton.addEventListener("click", () => {
  const message = messageInput.value.trim();
  if (message !== "") {
    // This is for creating a chat bubble for the user message
    const userBubble = document.createElement("div");
    userBubble.classList.add("chat-bubble", "user-bubble");

    if (passwordInput) {
      userBubble.textContent = "**********"
    }
    if (message) {
      userBubble.textContent = message;
      // This is to clear the input field
      messageInput.value = "";
    }

    // This is for appending the user bubble to the chat area
    chatArea.appendChild(userBubble);

    send(message)
  }
});

//For Handling File uploads
const fileUpload = document.getElementById("file-upload");

fileUpload.addEventListener("change", (event) => {
  if (event.target.files.length > 0) {
    const file = event.target.files[0];
    let fileInfo = {"name":file.name, "type":file.type, "size":file.size}
    console.log(file.name, file.type, file.size)
    const message = `I just sent a file 📔`;
    // This is for creating a chat bubble for the user message
    const userBubble = document.createElement("div");
    userBubble.classList.add("chat-bubble", "user-bubble");
    userBubble.textContent = message;

    // This is for appending the user bubble to the chat area
    const chatArea = document.querySelector(".chat-area");
    chatArea.appendChild(userBubble);

    // This is for clearing the input field
    messageInput.value = "";
    displaythumbnail(file)
    send(JSON.stringify(fileInfo))   
  } else {
    const botBubble = document.createElement("div");
    botBubble.classList.add("chat-bubble", "bot-bubble");
    botBubble.textContent = `You did not upload any File.`;
    chatArea.appendChild(botBubble);
    console.log("No file selected");
  }
});