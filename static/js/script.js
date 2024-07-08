document.getElementById('theme-toggle').addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
  });
  
  const chatBox = document.getElementById('chat-box');
  const messageInput = document.getElementById('chat-input');
  const sendButton = document.getElementById("send-button");
  
  const inactiveMessage = "Server is down, Please contact the developer to activate it";
  var host = "http://127.0.0.1:5005/chat";
//   let passwordInput = false;

// Adjusting the textarea height dynamically
  function autoGrowTextArea(textArea) {
    textArea.style.height = "auto";  // Reset height to re-measure
    textArea.style.height = textArea.scrollHeight + "px";  // Set new height
  }
  
  messageInput.addEventListener("input", () => {
    autoGrowTextArea(messageInput);  // Call on input to adjust height
  });
  
  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {  // Prevent 'Enter' from creating a new line unless 'Shift' is pressed
      event.preventDefault();  // Prevent the default action to avoid new line
      sendButton.click();  // Trigger the send button click
    }
  });
  
//   function replaceWithAsterisks(str) {
//     return '*'.repeat(str.length);
//   }
  
  function userResponseBtn(e) {
  send(e.value);
  }

  function createChatBubble(message) {
    const botMessage = document.createElement('div');
    botMessage.classList.add('chat-message', 'bot-message');
    botMessage.innerHTML = `<span>🤖 "${message}"</span>`;
    return botMessage
  }

  function setBotResponse(val, isFinal = false) {
    let botMessage = document.querySelector('.bot-message:last-child');
    if (!botMessage) {
        botMessage = createChatBubble(val);
        chatBox.appendChild(botMessage);
    } else {
        botMessage.querySelector('span').textContent = `🤖 "${val}"`;
    }

    if (isFinal) {
        messageInput.disabled = false;
    }
}

function send(message) {
    messageInput.type = "text";
    messageInput.focus();
    console.log("User Message:", message);

    // Show the spinner
    document.getElementById('spinner').style.display = 'block';
  
    // Disable the input field while the request is in progress
    messageInput.disabled = true;
  
    fetch(host, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "message": message,
            "sender": "User"
        })
    }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let result = '';
  
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    console.log("Stream complete");
                    setBotResponse(result, true); // Pass true when streaming is complete
                    // Hide the spinner
                    document.getElementById('spinner').style.display = 'none';
                    return;
                }
                result += decoder.decode(value);
                setBotResponse(result); // Update the chat bubble with the current content
                read();
            });
        }
        read();
    }).catch(error => {
        console.log('Error:', error);
        // Hide the spinner and handle error
        document.getElementById('spinner').style.display = 'none';
        setBotResponse(inactiveMessage, true);
        messageInput.disabled = false;
        // Optionally, display an error message in the chat interface
    });
}
  
  sendButton.addEventListener("click", () => {
    const message = messageInput.value.trim();
    if (message !== "") {
        // This is for creating a chat bubble for the user message
        const userMessage = document.createElement('div');
        userMessage.classList.add('chat-message', 'user-message');
        if (message) {
            userMessage.textContent = message;
            // This is to clear the input field
            messageInput.value = "";  // Clear the input field
            autoGrowTextArea(messageInput);  // Reset height after clearing
        }
  
        chatBox.appendChild(userMessage);
        send(message)
  
        chatBox.scrollTop = chatBox.scrollHeight;
    }
  });
  
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
    thumbnailBubble.classList.add('chat-message', 'bot-message', 'file-bubble');
    thumbnailBubble.appendChild(thumbnail);
  
    // Appending the bot bubble to the chat area
    setTimeout(() => {
      chatBox.appendChild(thumbnailBubble);
    }, 500);
  }
  //For Handling File uploads
  const fileUpload = document.getElementById("upload-file");
  
  // fileUpload.addEventListener("change", (event) => {
  //   if (event.target.files.length > 0) {
  //       const file = event.target.files[0];
  //       let fileInfo = {"name":file.name, "type":file.type, "size":file.size}
  //       console.log(file.name, file.type, file.size)
  //       const message = `I just sent a file 📔`;
  //       // This is for creating a chat bubble for the user message
  //       const userMessage = document.createElement("div");
  //       userMessage.classList.add('chat-message', 'user-message');
  //       userMessage.textContent = message;
  
  //       // This is for appending the user bubble to the chat area
  //       const chatBox = document.getElementById('chat-box');
  //       chatBox.appendChild(userMessage);
  
  //       // This is for clearing the input field
  //       messageInput.value = "";
  //       displaythumbnail(file)
  //       send(JSON.stringify(fileInfo))
  //       chatBox.scrollTop = chatBox.scrollHeight;
  
  //   } 
  //   else {
  //       const botMessage = document.createElement("div");
  //       botMessage.classList.add('chat-message', 'bot-message');
  //       botMessage.textContent = `You did not upload any File.`;
  //       chatBox.appendChild(botMessage);
  //       console.log("No file selected");
  //   }
  // });  
  
fileUpload.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file); // 'file' is the key

        // Send the file to the server
        fetch('/upload', { // Make sure the endpoint matches in Flask
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            let fileInfo = {"name":file.name, "type":file.type, "size":file.size}
            console.log(fileInfo)
            const message = `I just sent a file 📔`;
            // This is for creating a chat bubble for the user message
            const userMessage = document.createElement("div");
            userMessage.classList.add('chat-message', 'user-message');
            userMessage.textContent = message;
            // This is for appending the user bubble to the chat area
            chatBox.appendChild(userMessage);
  
            // This is for clearing the input field
            messageInput.value = "";
            displaythumbnail(file)
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
        });

        // Additional UI updates or notifications can be added here
    } else {
        console.log("No file selected");
        const botMessage = document.createElement("div");
        botMessage.classList.add('chat-message', 'bot-message');
        botMessage.textContent = `You did not upload any File.`;
        chatBox.appendChild(botMessage);
    }
});

  
  
  function restartChat() {
    const userMessage = document.createElement('div');
    userMessage.classList.add('chat-message', 'user-message');
    userMessage.textContent = "/restart";
    chatBox.append(userMessage)
    send("/restart")
    chatBox.scrollTop = chatBox.scrollHeight;
    chatBox.innerHTML = '';
  }