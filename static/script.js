let currentChatId = null;

// Toggle sidebar
document.getElementById('menuBtn').addEventListener('click', function() {
  const sidebar = document.getElementById('sidebar');
  const menuBtn = document.getElementById('menuBtn');
  sidebar.classList.toggle('open');
  menuBtn.classList.toggle('active');
});

// Send suggestion
function sendSuggestion(text) {
  document.getElementById('messageInput').value = text;
  sendMessage();
}

// Send message function
async function sendMessage() {
  const input = document.getElementById('messageInput');
  const messageText = input.value.trim();
  
  if (messageText === '') return;
  
  // Clear input immediately
  input.value = '';
  
  // Remove welcome message if exists
  const welcomeMsg = document.querySelector('.welcome-message');
  if (welcomeMsg) {
    welcomeMsg.remove();
  }
  
  // Display user message immediately
  addMessage(messageText, 'user');
  
  try {
    const response = await fetch('/api/send_message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message: messageText,
        chat_id: currentChatId 
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      currentChatId = data.chat_id;
      addMessage(data.bot_message.content, 'bot', data.bot_message.events);
      loadChats(); // Refresh chat list
    } else {
      addMessage('Error: ' + data.error, 'bot');
    }
  } catch (error) {
    console.error('Error:', error);
    addMessage('👻 Oops! The ghosts interfered with our connection. Please try again!', 'bot');
  }
}

// Get event icon based on title - Halloween themed
function getEventIcon(title) {
  const titleLower = title.toLowerCase();
  if (titleLower.includes('music') || titleLower.includes('concert') || titleLower.includes('band')) return '🎵';
  if (titleLower.includes('dance') || titleLower.includes('dj')) return '💃';
  if (titleLower.includes('food') || titleLower.includes('feast')) return '🍕';
  if (titleLower.includes('comedy') || titleLower.includes('stand')) return '😂';
  if (titleLower.includes('art') || titleLower.includes('paint')) return '🎨';
  if (titleLower.includes('game') || titleLower.includes('sport')) return '🎮';
  if (titleLower.includes('movie') || titleLower.includes('film')) return '🎬';
  if (titleLower.includes('workshop') || titleLower.includes('seminar')) return '📚';
  if (titleLower.includes('fashion') || titleLower.includes('style')) return '👗';
  if (titleLower.includes('tech') || titleLower.includes('innovation')) return '💻';
  if (titleLower.includes('horror') || titleLower.includes('scary')) return '😱';
  if (titleLower.includes('haunted') || titleLower.includes('ghost')) return '👻';
  if (titleLower.includes('trick') || titleLower.includes('treat')) return '🍬';
  if (titleLower.includes('costume') || titleLower.includes('dress')) return '🎭';
  return '🎃'; // Default Halloween icon
}

// Add message to UI with optional events
function addMessage(text, type, events = null) {
  const container = document.getElementById('messagesContainer');
  
  // Add text message
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;
  messageDiv.textContent = text;
  container.appendChild(messageDiv);
  
  // Add event cards if present
  if (events && events.length > 0) {
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'message bot-message';
    eventsContainer.style.maxWidth = '95%';
    eventsContainer.style.background = 'transparent';
    eventsContainer.style.border = 'none';
    eventsContainer.style.boxShadow = 'none';
    eventsContainer.style.padding = '0';
    
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'event-cards-container';
    
    events.forEach((event, index) => {
      const card = document.createElement('div');
      card.className = 'event-card';
      card.style.animationDelay = `${index * 0.1}s`;
      
      const icon = getEventIcon(event.title);
      
      card.innerHTML = `
        <div class="event-card-header">
          <span class="event-icon">${icon}</span>
          <div class="event-title">${event.title}</div>
        </div>
        <div class="event-details">
          <div class="event-detail-row">
            <span class="event-detail-icon">⏰</span>
            <span>${event.time}</span>
          </div>
          <div class="event-detail-row">
            <span class="event-detail-icon">📍</span>
            <span>${event.venue}</span>
          </div>
          ${event.description ? `
            <div class="event-detail-row">
              <span class="event-detail-icon">📝</span>
              <span>${event.description}</span>
            </div>
          ` : ''}
        </div>
      `;
      
      cardsContainer.appendChild(card);
    });
    
    eventsContainer.appendChild(cardsContainer);
    container.appendChild(eventsContainer);
  }
  
  // Smooth scroll to bottom
  setTimeout(() => {
    container.scrollTop = container.scrollHeight;
  }, 100);
}

// Load chats list
async function loadChats() {
  try {
    const response = await fetch('/api/get_chats');
    const data = await response.json();
    
    if (data.success) {
      const chatsList = document.getElementById('pastChatsList');
      chatsList.innerHTML = '';
      
      if (data.chats.length === 0) {
        chatsList.innerHTML = '<div style="color: #FFD4B3; padding: 20px; text-align: center; font-size: 14px;">No chats yet! Start your first spooky conversation 🎃</div>';
        return;
      }
      
      data.chats.forEach((chat, index) => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item';
        chatItem.textContent = chat.title;
        chatItem.style.animationDelay = `${index * 0.1}s`;
        chatItem.onclick = () => loadChat(chat.id);
        chatsList.appendChild(chatItem);
      });
    }
  } catch (error) {
    console.error('Error loading chats:', error);
  }
}

// Load specific chat
async function loadChat(chatId) {
  try {
    const response = await fetch(`/api/get_chat/${chatId}`);
    const data = await response.json();
    
    if (data.success) {
      currentChatId = chatId;
      const container = document.getElementById('messagesContainer');
      container.innerHTML = '';
      
      data.chat.messages.forEach(msg => {
        addMessage(msg.content, msg.type, msg.events);
      });
      
      // Close sidebar on mobile after selecting chat
      if (window.innerWidth < 768) {
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('menuBtn').classList.remove('active');
      }
    }
  } catch (error) {
    console.error('Error loading chat:', error);
  }
}

// New chat button
document.getElementById('newChatBtn').addEventListener('click', function() {
  currentChatId = null;
  const container = document.getElementById('messagesContainer');
  container.innerHTML = `
    <div class="welcome-message">
      <div class="welcome-icon">🎃</div>
      <h2>New Haunted Chat Started!</h2>
      <p>Let's find some spooky events! 🦇</p>
      <div class="welcome-suggestions">
        <button class="suggestion-btn" onclick="sendSuggestion('Show all events')">
          🎃 Show all events
        </button>
        <button class="suggestion-btn" onclick="sendSuggestion('What\\'s happening now?')">
          ⏰ What's happening now?
        </button>
        <button class="suggestion-btn" onclick="sendSuggestion('Next event')">
          🦇 Next event
        </button>
      </div>
    </div>
  `;
  document.getElementById('messageInput').focus();
  
  // Close sidebar on mobile
  if (window.innerWidth < 768) {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('menuBtn').classList.remove('active');
  }
});

// Account button
document.getElementById('accountBtn').addEventListener('click', async function() {
  try {
    const response = await fetch('/api/account');
    const data = await response.json();
    
    if (data.success) {
      const accountInfo = `🎃 Account Information 🎃
━━━━━━━━━━━━━━━━━━
🧛 User ID: ${data.account.user_id}
💬 Total Chats: ${data.account.total_chats}
📅 Member Since: ${new Date(data.account.created_at).toLocaleDateString()}

Keep the spooky party going! 👻`;
      alert(accountInfo);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('❌ Failed to load account information');
  }
});

// Report button
document.getElementById('reportBtn').addEventListener('click', async function() {
  const reportText = prompt('🕷️ Share your feedback or report an issue:');
  
  if (reportText && reportText.trim()) {
    try {
      const response = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report: reportText })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('✅ Thank you for your feedback! We appreciate it! 🎃');
      } else {
        alert('❌ Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Failed to submit feedback. Please try again.');
    }
  }
});

// Send on Enter key
document.getElementById('messageInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Send button click
document.getElementById('sendBtn').addEventListener('click', sendMessage);

// Focus input on load
document.getElementById('messageInput').focus();

// Load chats on page load
loadChats();

// Auto-resize on window resize
window.addEventListener('resize', function() {
  if (window.innerWidth > 768) {
    // Keep sidebar open on desktop
  }
});



let chatData = [
  { sender: "User", message: "Hey bot!" },
  { sender: "Bot", message: "Hi there 👋" }
];

// When tab or window is closed
window.addEventListener('beforeunload', function (e) {
  try {
    // Convert chatData to JSON and send to backend
    navigator.sendBeacon("/save-chat", JSON.stringify(chatData));
  } catch (err) {
    console.error("Error sending chat data before unload:", err);
  }
});