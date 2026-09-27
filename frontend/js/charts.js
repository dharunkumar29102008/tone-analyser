/**
 * CEREBRO — Chart.js Visualizations
 */

const Charts = {
  distributionChart: null,
  timelineChart: null,

  // Emotion color palette matching the UI reference
  colors: {
    frustration: '#f43f5e',
    sarcasm: '#f59e0b',
    calm: '#06b6d4',
    hopeful: '#10b981',
    passive_aggressive: '#a855f7',
    neutral: '#64748b',
    anger: '#ef4444',
    joy: '#38bdf8'
  },

  renderEmotionDistribution(distributionData, totalMessages) {
    const canvas = document.getElementById('emotion-donut-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (this.distributionChart) {
      this.distributionChart.destroy();
    }

    const labels = [];
    const values = [];
    const bgColors = [];

    for (const [key, item] of Object.entries(distributionData)) {
      if (item.count > 0) {
        labels.push(item.name);
        values.push(item.count);
        bgColors.push(this.colors[key] || '#8b5cf6');
      }
    }

    // Update center label
    const centerCountEl = document.getElementById('donut-center-count');
    if (centerCountEl) {
      centerCountEl.innerText = totalMessages;
    }

    this.distributionChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: '#0f1629',
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#111a33',
            titleColor: '#ffffff',
            bodyColor: '#94a3b8',
            borderColor: '#2c3c66',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const val = context.raw || 0;
                const pct = Math.round((val / total) * 100);
                return ` ${context.label}: ${pct}% (${val})`;
              }
            }
          }
        }
      }
    });
  },

  renderEmotionArc(timelineData) {
    const canvas = document.getElementById('emotion-arc-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (this.timelineChart) {
      this.timelineChart.destroy();
    }

    const labels = timelineData.map((d, i) => `#${d.index || i + 1} ${d.sender}`);
    const intensities = timelineData.map(d => d.intensity);
    const escalations = timelineData.map(d => d.escalation);

    // Gradient fill for intensity
    const gradient = ctx.createLinearGradient(0, 0, 0, 350);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.45)');
    gradient.addColorStop(0.7, 'rgba(139, 92, 246, 0.08)');
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');

    // Point radius and styles for shifts
    const pointRadii = timelineData.map(d => (d.is_shift ? 7 : (d.is_trigger ? 8 : 4)));
    const pointColors = timelineData.map(d => {
      if (d.is_trigger) return '#ef4444'; // Red trigger dot
      if (d.is_shift) return '#f59e0b'; // Amber shift dot
      return '#8b5cf6';
    });

    this.timelineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Emotional Intensity',
            data: intensities,
            borderColor: '#a855f7',
            backgroundColor: gradient,
            borderWidth: 3,
            fill: true,
            tension: 0.35,
            pointRadius: pointRadii,
            pointBackgroundColor: pointColors,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 1.5,
            pointHoverRadius: 9
          },
          {
            label: 'Escalation Level',
            data: escalations,
            borderColor: '#f43f5e',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.3,
            pointRadius: 2,
            pointBackgroundColor: '#f43f5e'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        scales: {
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.04)'
            },
            ticks: {
              color: '#64748b',
              font: { size: 11 }
            }
          },
          y: {
            min: 0,
            max: 100,
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#64748b',
              callback(value) {
                return value + '%';
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#111a33',
            titleColor: '#38bdf8',
            bodyColor: '#f1f5f9',
            borderColor: '#2c3c66',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              title(items) {
                const idx = items[0].dataIndex;
                const d = timelineData[idx];
                return `${d.sender} (${d.timestamp})`;
              },
              afterTitle(items) {
                const idx = items[0].dataIndex;
                const d = timelineData[idx];
                return `"${d.text.length > 55 ? d.text.slice(0, 55) + '...' : d.text}"`;
              },
              label(context) {
                return ` ${context.dataset.label}: ${context.raw}%`;
              },
              afterBody(items) {
                const idx = items[0].dataIndex;
                const d = timelineData[idx];
                const notes = [];
                notes.push(`Tone: ${d.tone} | Emotion: ${d.emotion}`);
                if (d.is_shift) {
                  notes.push(`⚠ Significant Tone Shift: ${d.shift_note || ''}`);
                }
                if (d.is_trigger) {
                  notes.push(`⚡ Trigger Event identified`);
                }
                return notes;
              }
            }
          }
        }
      }
    });
  }
};
