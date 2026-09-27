/**
 * CEREBRO — Intelligence Dashboard Renderer
 */

const Dashboard = {
  renderHighlights(highlights) {
    const list = document.getElementById('highlights-list');
    if (!list) return;
    list.innerHTML = '';

    if (!highlights || highlights.length === 0) {
      list.innerHTML = '<div style="color: var(--text-dim); font-size: 0.8rem; padding: 8px;">No major highlights detected yet.</div>';
      return;
    }

    highlights.forEach(h => {
      const row = document.createElement('div');
      row.className = 'highlight-row';
      row.innerHTML = `
        <div class="highlight-main-group">
          <div class="highlight-emoji">${h.emoji || '⚡'}</div>
          <div class="highlight-text-content">
            <span class="highlight-title">${this.escapeHtml(h.title)}</span>
            <span class="highlight-quote">${this.escapeHtml(h.quote)}</span>
          </div>
        </div>
        <span class="highlight-time">${this.escapeHtml(h.timestamp)}</span>
      `;

      // Click to scroll to the message
      row.addEventListener('click', () => {
        Conversation.scrollToMessage(h.message_id);
      });

      list.appendChild(row);
    });
  },

  renderDistributionLegend(distributionData) {
    const legendList = document.getElementById('emotion-legend-list');
    if (!legendList) return;
    legendList.innerHTML = '';

    for (const [key, item] of Object.entries(distributionData)) {
      const row = document.createElement('div');
      row.className = 'emotion-legend-item';
      row.innerHTML = `
        <div class="emotion-name-group">
          <span>${item.emoji || '💬'}</span>
          <span>${this.escapeHtml(item.name)}</span>
        </div>
        <div class="emotion-value-group">
          <span class="emotion-pct">${item.percentage}%</span>
          <span class="emotion-count">(${item.count})</span>
        </div>
      `;
      legendList.appendChild(row);
    }
  },

  renderInsights(insights) {
    const list = document.getElementById('conversation-insights-list');
    if (!list) return;
    list.innerHTML = '';

    if (!insights || insights.length === 0) {
      list.innerHTML = '<li>Analyzing conversation flow...</li>';
      return;
    }

    insights.forEach(insight => {
      const li = document.createElement('li');
      li.innerText = insight;
      list.appendChild(li);
    });
  },

  renderKeyMoments(keyMoments) {
    const grid = document.getElementById('key-moments-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (!keyMoments || keyMoments.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-dim); padding: 20px;">No critical trigger moments identified.</div>';
      return;
    }

    keyMoments.forEach(km => {
      const card = document.createElement('div');
      card.className = 'moment-card';

      let tagClass = 'tag-shift';
      if (km.shift_type === 'de_escalation_recovery') tagClass = 'tag-recovery';
      else if (km.shift_type === 'negative_escalation') tagClass = 'tag-escalation';

      card.innerHTML = `
        <div class="moment-header">
          <span class="moment-tag ${tagClass}">${this.escapeHtml(km.shift_type.replace('_', ' '))}</span>
          <span style="font-size: 0.75rem; color: var(--text-dim);">${this.escapeHtml(km.timestamp)}</span>
        </div>
        
        <h4 style="font-size: 1rem; color: #ffffff; font-weight: 700;">${this.escapeHtml(km.title)}</h4>
        
        <div class="moment-flow-container">
          <!-- Before State -->
          <div class="flow-step">
            <span class="flow-step-label">Before State</span>
            <span class="flow-state-val">${this.escapeHtml(km.before_state.emotion)}</span>
            <span style="font-size: 0.72rem; color: var(--text-dim);">Intensity: ${this.escapeHtml(km.before_state.intensity)}</span>
          </div>

          <div class="flow-arrow">→</div>

          <!-- Trigger Message -->
          <div class="flow-step trigger">
            <span class="flow-step-label" style="color: #c084fc;">Trigger Statement</span>
            <span class="flow-trigger-quote">"${this.escapeHtml(km.quote)}"</span>
            <span style="font-size: 0.72rem; color: #94a3b8; margin-top: 2px;">— ${this.escapeHtml(km.sender)}</span>
          </div>

          <div class="flow-arrow">→</div>

          <!-- After State -->
          <div class="flow-step">
            <span class="flow-step-label">After State</span>
            <span class="flow-state-val">${this.escapeHtml(km.after_state.emotion)}</span>
            <span style="font-size: 0.72rem; color: var(--text-dim);">Intensity: ${this.escapeHtml(km.after_state.intensity)}</span>
          </div>
        </div>

        <div class="moment-interpretation">
          <strong style="color: #c084fc; font-size: 0.78rem; display: block; margin-bottom: 2px;">Cerebro's Interpretation</strong>
          ${this.escapeHtml(km.cerebro_interpretation)}
        </div>

        <div style="display: flex; justify-content: flex-end;">
          <button class="btn btn-secondary btn-sm" onclick="Conversation.scrollToMessage(${km.trigger_message_id})">
            View in Chat
          </button>
        </div>
      `;
      grid.appendChild(card);
    });
  },

  renderParticipants(participantsAnalysis) {
    const grid = document.getElementById('participants-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (!participantsAnalysis || participantsAnalysis.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-dim);">No participant data available.</div>';
      return;
    }

    participantsAnalysis.forEach(p => {
      const card = document.createElement('div');
      card.className = 'participant-stat-card';
      const initials = Utils.getInitials(p.name);
      const grad = Utils.getAvatarGradient(p.name);

      card.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="message-avatar" style="background: ${grad}">${initials}</div>
          <div>
            <h4 style="font-size: 0.95rem; font-weight: 700; color: #ffffff;">${this.escapeHtml(p.name)}</h4>
            <span style="font-size: 0.75rem; color: var(--text-dim);">${p.message_count} messages sent</span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 4px;">
          <div style="background: rgba(255,255,255,0.02); padding: 8px 10px; border-radius: 8px;">
            <span style="font-size: 0.7rem; color: var(--text-dim); display: block;">Avg. Intensity</span>
            <span style="font-size: 1.05rem; font-weight: 800; color: #38bdf8;">${p.avg_intensity}%</span>
          </div>
          <div style="background: rgba(255,255,255,0.02); padding: 8px 10px; border-radius: 8px;">
            <span style="font-size: 0.7rem; color: var(--text-dim); display: block;">Dominant Tone</span>
            <span class="tone-badge badge-${p.tone_badge_variant}" style="margin-top: 2px;">${this.escapeHtml(p.dominant_tone)}</span>
          </div>
        </div>

        <div style="font-size: 0.74rem; color: var(--text-muted); display: flex; justify-content: space-between; margin-top: 4px;">
          <span>Pos: ${p.sentiment_ratio.positive}%</span>
          <span>Neu: ${p.sentiment_ratio.neutral}%</span>
          <span>Neg: ${p.sentiment_ratio.negative}%</span>
        </div>
      `;
      grid.appendChild(card);
    });
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
