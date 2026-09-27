/**
 * CEREBRO — Conversation Stream and Replay Engine
 */

const Conversation = {
  currentMessages: [],
  activeFilter: 'all',
  replayInterval: null,
  isReplaying: false,
  replayIndex: 0,

  renderHeader(filename, messageCount) {
    const fileEl = document.getElementById('chat-filename');
    const metaEl = document.getElementById('chat-file-meta');
    if (fileEl) fileEl.innerText = filename || 'chat.txt';
    if (metaEl) metaEl.innerText = `WhatsApp Export • ${messageCount} messages`;
  },

  renderMessages(messages, filterSender = 'all') {
    this.currentMessages = messages;
    this.activeFilter = filterSender;

    const stream = document.getElementById('chat-stream');
    if (!stream) return;
    stream.innerHTML = '';

    const filtered = filterSender === 'all'
      ? messages
      : messages.filter(m => m.sender === filterSender);

    filtered.forEach(msg => {
      const card = this.createMessageCard(msg);
      stream.appendChild(card);
    });

    // Populate participant filter dropdown
    this.updateFilterDropdown(messages);
  },

  createMessageCard(msg) {
    const card = document.createElement('div');
    card.className = 'message-card';
    card.id = `msg-card-${msg.id}`;

    const initials = Utils.getInitials(msg.sender);
    const avatarGrad = Utils.getAvatarGradient(msg.sender);

    // Badge variant class
    const variant = msg.badge ? msg.badge.variant : 'neutral';
    const badgeText = msg.badge ? msg.badge.text : 'Neutral';

    card.innerHTML = `
      <div class="message-avatar" style="background: ${avatarGrad}">
        ${initials}
      </div>
      <div class="message-body">
        <div class="message-meta-row">
          <div class="message-sender-group">
            <span class="sender-name">${this.escapeHtml(msg.sender)}</span>
            <span class="message-time">${this.escapeHtml(msg.timestamp)}</span>
          </div>
          <span class="tone-badge badge-${variant}">
            ${this.escapeHtml(badgeText)}
          </span>
        </div>
        <div class="message-text">${this.escapeHtml(msg.text)}</div>
      </div>
    `;

    // Click to view message context
    card.addEventListener('click', () => {
      this.showCues(msg);
    });

    return card;
  },

  showCues(msg) {
    if (msg.cues && msg.cues.length > 0) {
      Utils.showToast(`Message #${msg.id} cues: ${msg.cues.join(' • ')}`, 'info');
    }
  },

  updateFilterDropdown(messages) {
    const dropdown = document.getElementById('participant-filter');
    if (!dropdown) return;

    const participants = Array.from(new Set(messages.map(m => m.sender)));
    const currentValue = dropdown.value;

    dropdown.innerHTML = '<option value="all">All Participants</option>';
    participants.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.innerText = p;
      dropdown.appendChild(opt);
    });

    dropdown.value = participants.includes(currentValue) ? currentValue : 'all';
  },

  scrollToMessage(id) {
    const card = document.getElementById(`msg-card-${id}`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.remove('highlight-focus');
      void card.offsetWidth; // Trigger reflow
      card.classList.add('highlight-focus');
      setTimeout(() => card.classList.remove('highlight-focus'), 2500);
    }
  },

  // Interactive Conversation Replay Mode
  startReplay(messages, onStepCallback) {
    if (this.isReplaying) {
      this.stopReplay();
      return;
    }

    const stream = document.getElementById('chat-stream');
    if (!stream || messages.length === 0) return;

    stream.innerHTML = '';
    this.isReplaying = true;
    this.replayIndex = 0;

    const replayBtn = document.getElementById('btn-replay');
    if (replayBtn) {
      replayBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
        Pause
      `;
    }

    this.replayInterval = setInterval(() => {
      if (this.replayIndex >= messages.length) {
        this.stopReplay();
        Utils.showToast('Conversation replay complete', 'success');
        return;
      }

      const msg = messages[this.replayIndex];
      const card = this.createMessageCard(msg);
      stream.appendChild(card);
      card.scrollIntoView({ behavior: 'smooth', block: 'end' });

      if (onStepCallback) {
        onStepCallback(messages.slice(0, this.replayIndex + 1), msg);
      }

      this.replayIndex++;
    }, 900);
  },

  stopReplay() {
    if (this.replayInterval) {
      clearInterval(this.replayInterval);
      this.replayInterval = null;
    }
    this.isReplaying = false;
    const replayBtn = document.getElementById('btn-replay');
    if (replayBtn) {
      replayBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Replay
      `;
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
};
