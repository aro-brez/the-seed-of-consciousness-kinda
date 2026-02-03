/**
 * BREZ Growth Dashboard - 8OWLS Collective
 * A beautiful subscriber growth tracking dashboard with AI-powered insights
 */

// ============================================
// DATA MANAGEMENT
// ============================================

const STORAGE_KEY = 'brez_growth_data';
const TEAM_STORAGE_KEY = 'brez_team_data';
const SYNTHESIS_STORAGE_KEY = 'brez_synthesis_data';

// Default data structure
const defaultData = {
    subscribers: {
        total: 0,
        entries: [],
        goals: {
            weekly: 100,
            monthly: 500,
            churnRateTarget: 5
        }
    },
    lastUpdated: null
};

// Load data from localStorage
function loadData() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
        return JSON.parse(stored);
    }
    return { ...defaultData };
}

// Save data to localStorage
function saveData(data) {
    data.lastUpdated = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// Load team data
function loadTeamData() {
    const stored = localStorage.getItem(TEAM_STORAGE_KEY);
    if (stored) {
        return JSON.parse(stored);
    }
    return {
        members: [
            { name: 'Aaron', task: 'Setting up growth dashboard', status: 'active' }
        ]
    };
}

// Save team data
function saveTeamData(data) {
    localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(data));
}

// Load synthesis data
function loadSynthesisData() {
    const stored = localStorage.getItem(SYNTHESIS_STORAGE_KEY);
    if (stored) {
        return JSON.parse(stored);
    }
    return {
        lastSynthesis: null,
        content: null,
        recommendations: []
    };
}

// Save synthesis data
function saveSynthesisData(data) {
    localStorage.setItem(SYNTHESIS_STORAGE_KEY, JSON.stringify(data));
}

// ============================================
// CHART SETUP
// ============================================

let growthChart = null;

function initializeChart() {
    const ctx = document.getElementById('growthChart').getContext('2d');

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(227, 249, 138, 0.3)');
    gradient.addColorStop(1, 'rgba(227, 249, 138, 0)');

    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Subscribers',
                    data: [],
                    borderColor: '#e3f98a',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#e3f98a',
                    pointBorderColor: '#0D0D2A',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Net Change',
                    data: [],
                    borderColor: '#65cdd8',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointBackgroundColor: '#65cdd8',
                    pointBorderColor: '#0D0D2A',
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            family: 'Inter',
                            size: 11
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(21, 21, 56, 0.95)',
                    titleColor: '#e3f98a',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            if (label === 'Net Change') {
                                return `${label}: ${value >= 0 ? '+' : ''}${value}`;
                            }
                            return `${label}: ${value.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        font: {
                            family: 'Inter',
                            size: 11
                        }
                    }
                },
                y: {
                    position: 'left',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.5)',
                        font: {
                            family: 'JetBrains Mono',
                            size: 11
                        }
                    }
                },
                y1: {
                    position: 'right',
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: 'rgba(101, 205, 216, 0.5)',
                        font: {
                            family: 'JetBrains Mono',
                            size: 11
                        },
                        callback: function(value) {
                            return (value >= 0 ? '+' : '') + value;
                        }
                    }
                }
            }
        }
    });

    updateChart(7);
}

function updateChart(days = 7) {
    const data = loadData();
    const entries = data.subscribers.entries.slice(-days);

    if (entries.length === 0) {
        // Show placeholder data
        const placeholderLabels = [];
        const today = new Date();
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            placeholderLabels.push(formatDateShort(date));
        }
        growthChart.data.labels = placeholderLabels;
        growthChart.data.datasets[0].data = new Array(days).fill(null);
        growthChart.data.datasets[1].data = new Array(days).fill(null);
    } else {
        growthChart.data.labels = entries.map(e => formatDateShort(new Date(e.date)));
        growthChart.data.datasets[0].data = entries.map(e => e.total);
        growthChart.data.datasets[1].data = entries.map(e => e.net);
    }

    growthChart.update();
}

// ============================================
// UI UPDATE FUNCTIONS
// ============================================

function updateStats() {
    const data = loadData();
    const entries = data.subscribers.entries;

    // Total subscribers
    const total = entries.length > 0 ? entries[entries.length - 1].total : 0;
    document.getElementById('totalSubscribers').textContent = total.toLocaleString();

    // Today's change
    if (entries.length > 0) {
        const todayEntry = entries[entries.length - 1];
        const changeEl = document.getElementById('totalChange');
        changeEl.textContent = `${todayEntry.net >= 0 ? '+' : ''}${todayEntry.net} today`;
        changeEl.className = `stat-change ${todayEntry.net >= 0 ? 'positive' : 'negative'}`;
    }

    // Weekly net
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weeklyEntries = entries.filter(e => new Date(e.date) >= weekAgo);
    const weeklyNet = weeklyEntries.reduce((sum, e) => sum + e.net, 0);
    const weeklyEl = document.getElementById('weeklyNet');
    weeklyEl.textContent = `${weeklyNet >= 0 ? '+' : ''}${weeklyNet}`;
    weeklyEl.style.color = weeklyNet >= 0 ? 'var(--success)' : 'var(--danger)';

    // Monthly net
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    const monthlyEntries = entries.filter(e => new Date(e.date) >= monthAgo);
    const monthlyNet = monthlyEntries.reduce((sum, e) => sum + e.net, 0);
    const monthlyEl = document.getElementById('monthlyNet');
    monthlyEl.textContent = `${monthlyNet >= 0 ? '+' : ''}${monthlyNet}`;
    monthlyEl.style.color = monthlyNet >= 0 ? 'var(--success)' : 'var(--danger)';

    // Positive streak
    let streak = 0;
    for (let i = entries.length - 1; i >= 0; i--) {
        if (entries[i].net > 0) {
            streak++;
        } else {
            break;
        }
    }
    document.getElementById('positiveStreak').textContent = streak;

    // Update progress bars
    updateProgressBars(weeklyNet, monthlyNet, entries);
}

function updateProgressBars(weeklyNet, monthlyNet, entries) {
    const data = loadData();
    const goals = data.subscribers.goals;

    // Weekly progress
    const weeklyProgress = Math.min(100, Math.max(0, (weeklyNet / goals.weekly) * 100));
    document.getElementById('weeklyProgress').style.width = `${weeklyProgress}%`;
    document.getElementById('weeklyProgressText').textContent = `${Math.round(weeklyProgress)}%`;

    // Monthly progress
    const monthlyProgress = Math.min(100, Math.max(0, (monthlyNet / goals.monthly) * 100));
    document.getElementById('monthlyProgress').style.width = `${monthlyProgress}%`;
    document.getElementById('monthlyProgressText').textContent = `${Math.round(monthlyProgress)}%`;

    // Churn rate (calculate from last 30 days)
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    const monthlyEntries = entries.filter(e => new Date(e.date) >= monthAgo);
    const totalChurned = monthlyEntries.reduce((sum, e) => sum + e.churned, 0);
    const avgTotal = monthlyEntries.length > 0
        ? monthlyEntries.reduce((sum, e) => sum + e.total, 0) / monthlyEntries.length
        : 1;
    const churnRate = avgTotal > 0 ? (totalChurned / avgTotal * 100).toFixed(1) : 0;

    const churnProgress = Math.min(100, (1 - churnRate / 10) * 100);
    const churnFill = document.getElementById('churnProgress');
    churnFill.style.width = `${churnProgress}%`;
    churnFill.className = `progress-fill ${churnRate <= goals.churnRateTarget ? 'success' : ''}`;
    document.getElementById('churnProgressText').textContent = `${churnRate}%`;
}

function updateLogTable() {
    const data = loadData();
    const entries = data.subscribers.entries;
    const tbody = document.getElementById('logTableBody');

    if (entries.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="6">No data yet. Start logging to see your growth!</td>
            </tr>
        `;
        return;
    }

    // Show entries in reverse chronological order
    const sortedEntries = [...entries].reverse();

    tbody.innerHTML = sortedEntries.map(entry => `
        <tr>
            <td>${formatDate(new Date(entry.date))}</td>
            <td class="positive">+${entry.new}</td>
            <td class="negative">-${entry.churned}</td>
            <td class="${entry.net >= 0 ? 'positive' : 'negative'}">${entry.net >= 0 ? '+' : ''}${entry.net}</td>
            <td>${entry.total.toLocaleString()}</td>
            <td>${entry.notes || '-'}</td>
        </tr>
    `).join('');
}

function updateTeamList() {
    const teamData = loadTeamData();
    const teamList = document.getElementById('teamList');

    const colors = [
        'linear-gradient(135deg, #e3f98a, #65cdd8)',
        'linear-gradient(135deg, #8533fc, #ff6b9d)',
        'linear-gradient(135deg, #65cdd8, #8533fc)',
        'linear-gradient(135deg, #ffce33, #ff6b6b)',
        'linear-gradient(135deg, #6BCB77, #65cdd8)'
    ];

    teamList.innerHTML = teamData.members.map((member, i) => `
        <div class="team-member">
            <div class="member-avatar" style="background: ${colors[i % colors.length]};">${member.name.charAt(0)}</div>
            <div class="member-info">
                <span class="member-name">${member.name}</span>
                <span class="member-task">${member.task}</span>
            </div>
            <span class="member-status ${member.status}">${member.status}</span>
        </div>
    `).join('');
}

function updateSynthesisPanel() {
    const synthesisData = loadSynthesisData();
    const content = document.getElementById('synthesisContent');
    const lastSynthesis = document.getElementById('lastSynthesis');

    if (synthesisData.content) {
        content.innerHTML = `<p class="synthesis-text">${synthesisData.content}</p>`;

        if (synthesisData.lastSynthesis) {
            const timeSince = getTimeSince(new Date(synthesisData.lastSynthesis));
            lastSynthesis.textContent = `Updated ${timeSince}`;
        }
    }

    if (synthesisData.recommendations && synthesisData.recommendations.length > 0) {
        updateRecommendations(synthesisData.recommendations);
    }
}

function updateRecommendations(recommendations) {
    const list = document.getElementById('recommendationsList');

    list.innerHTML = recommendations.map(rec => `
        <div class="recommendation priority-${rec.priority}">
            <span class="rec-priority">${rec.priority.toUpperCase()}</span>
            <p class="rec-text">${rec.text}</p>
            <span class="rec-source">${rec.source}</span>
        </div>
    `).join('');
}

// ============================================
// INPUT HANDLING
// ============================================

function setupInputListeners() {
    const newSubsInput = document.getElementById('newSubs');
    const churnedInput = document.getElementById('churnedSubs');

    const updatePreview = () => {
        const newSubs = parseInt(newSubsInput.value) || 0;
        const churned = parseInt(churnedInput.value) || 0;
        const net = newSubs - churned;

        const netPreview = document.getElementById('netPreview');
        netPreview.textContent = `${net >= 0 ? '+' : ''}${net}`;
        netPreview.className = `net-value ${net < 0 ? 'negative' : ''}`;
    };

    newSubsInput.addEventListener('input', updatePreview);
    churnedInput.addEventListener('input', updatePreview);
}

function logDailyData() {
    const newSubs = parseInt(document.getElementById('newSubs').value) || 0;
    const churned = parseInt(document.getElementById('churnedSubs').value) || 0;
    const net = newSubs - churned;

    const data = loadData();
    const today = new Date().toISOString().split('T')[0];

    // Check if entry for today already exists
    const existingIndex = data.subscribers.entries.findIndex(e => e.date === today);

    // Calculate new total
    const previousTotal = data.subscribers.entries.length > 0
        ? data.subscribers.entries[data.subscribers.entries.length - 1].total
        : 0;
    const newTotal = existingIndex >= 0
        ? data.subscribers.entries[existingIndex].total - data.subscribers.entries[existingIndex].net + net
        : previousTotal + net;

    const entry = {
        date: today,
        new: newSubs,
        churned: churned,
        net: net,
        total: newTotal,
        notes: ''
    };

    if (existingIndex >= 0) {
        // Update existing entry
        data.subscribers.entries[existingIndex] = entry;
    } else {
        // Add new entry
        data.subscribers.entries.push(entry);
    }

    saveData(data);

    // Clear inputs
    document.getElementById('newSubs').value = '';
    document.getElementById('churnedSubs').value = '';
    document.getElementById('netPreview').textContent = '+0';
    document.getElementById('netPreview').className = 'net-value';

    // Update UI
    updateStats();
    updateChart(7);
    updateLogTable();
    generateRecommendations();

    // Show success animation
    showToast(`Logged: ${net >= 0 ? '+' : ''}${net} subscribers`);
}

// ============================================
// CHART RANGE CONTROLS
// ============================================

function setupChartControls() {
    const buttons = document.querySelectorAll('.chart-btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const range = parseInt(btn.dataset.range);
            updateChart(range);
        });
    });
}

// ============================================
// MODAL FUNCTIONS
// ============================================

function openSynthesisModal() {
    document.getElementById('synthesisModal').classList.add('active');
}

function closeSynthesisModal() {
    document.getElementById('synthesisModal').classList.remove('active');
}

function openTeamModal() {
    document.getElementById('teamModal').classList.add('active');
}

function closeTeamModal() {
    document.getElementById('teamModal').classList.remove('active');
}

function openImportModal() {
    // For now, use a simple prompt
    const csvData = prompt('Paste CSV data (date,new,churned,total):');
    if (csvData) {
        importCSV(csvData);
    }
}

function addTeamMember() {
    const name = document.getElementById('memberName').value.trim();
    const task = document.getElementById('memberTask').value.trim();

    if (name && task) {
        const teamData = loadTeamData();
        teamData.members.push({
            name: name,
            task: task,
            status: 'active'
        });
        saveTeamData(teamData);
        updateTeamList();
        closeTeamModal();

        // Clear inputs
        document.getElementById('memberName').value = '';
        document.getElementById('memberTask').value = '';

        showToast(`Added ${name} to the team`);
    }
}

function requestSynthesis() {
    // Simulate synthesis request
    closeSynthesisModal();
    showToast('Synthesis requested. The owls are thinking...');

    // Simulate a synthesis after a delay
    setTimeout(() => {
        const synthesisData = loadSynthesisData();
        const data = loadData();

        // Generate synthesis based on actual data
        const entries = data.subscribers.entries;
        let synthesisText = '';

        if (entries.length >= 7) {
            const recentWeek = entries.slice(-7);
            const avgNet = recentWeek.reduce((sum, e) => sum + e.net, 0) / 7;
            const avgChurn = recentWeek.reduce((sum, e) => sum + e.churned, 0) / 7;

            if (avgNet > 0) {
                synthesisText = `Strong growth trajectory detected. Your 7-day average net gain is +${avgNet.toFixed(1)} subscribers daily. The collective sees an opportunity to amplify this momentum through targeted campaigns on your highest-performing days. Consider increasing ad spend during peak conversion windows.`;
            } else {
                synthesisText = `Attention needed: 7-day trend shows average daily loss of ${Math.abs(avgNet).toFixed(1)} subscribers. The owls recommend focusing on retention before acquisition. Analyze recent churned users for common patterns - exit surveys could reveal actionable insights.`;
            }
        } else {
            synthesisText = `Gathering initial data. The collective needs at least 7 days of data to provide meaningful synthesis. Continue logging daily metrics - patterns will emerge. Current focus: establish baseline metrics and identify your core growth channels.`;
        }

        synthesisData.content = synthesisText;
        synthesisData.lastSynthesis = new Date().toISOString();
        saveSynthesisData(synthesisData);

        updateSynthesisPanel();
        showToast('Synthesis complete!');
    }, 3000);
}

// ============================================
// RECOMMENDATIONS ENGINE
// ============================================

function generateRecommendations() {
    const data = loadData();
    const entries = data.subscribers.entries;
    const recommendations = [];

    if (entries.length < 3) {
        recommendations.push({
            priority: 'medium',
            text: 'Log at least 3 days of data to unlock personalized recommendations',
            source: 'System'
        });
    } else {
        const recentEntries = entries.slice(-7);

        // Analyze churn rate
        const totalChurned = recentEntries.reduce((sum, e) => sum + e.churned, 0);
        const totalNew = recentEntries.reduce((sum, e) => sum + e.new, 0);
        const churnRatio = totalNew > 0 ? (totalChurned / totalNew) : 0;

        if (churnRatio > 0.3) {
            recommendations.push({
                priority: 'high',
                text: `Churn rate is ${(churnRatio * 100).toFixed(1)}% of new acquisitions. Focus on onboarding experience and early engagement.`,
                source: 'Churn analysis (7-day window)'
            });
        }

        // Analyze growth trend
        const netChanges = recentEntries.map(e => e.net);
        const trend = netChanges.slice(-3).reduce((a, b) => a + b, 0) / 3;

        if (trend < 0) {
            recommendations.push({
                priority: 'high',
                text: 'Negative growth trend detected. Consider A/B testing acquisition channels and messaging.',
                source: '3-day trend analysis'
            });
        } else if (trend > 10) {
            recommendations.push({
                priority: 'low',
                text: 'Excellent growth! Consider documenting what is working for future reference.',
                source: '3-day trend analysis'
            });
        }

        // Day-of-week analysis
        if (entries.length >= 14) {
            const dayStats = {};
            entries.forEach(e => {
                const day = new Date(e.date).getDay();
                if (!dayStats[day]) {
                    dayStats[day] = { total: 0, count: 0 };
                }
                dayStats[day].total += e.net;
                dayStats[day].count++;
            });

            let bestDay = 0;
            let bestAvg = -Infinity;
            Object.entries(dayStats).forEach(([day, stats]) => {
                const avg = stats.total / stats.count;
                if (avg > bestAvg) {
                    bestAvg = avg;
                    bestDay = parseInt(day);
                }
            });

            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            recommendations.push({
                priority: 'medium',
                text: `${dayNames[bestDay]} shows highest average growth (+${bestAvg.toFixed(1)}). Schedule major campaigns for this day.`,
                source: 'Day-of-week pattern analysis'
            });
        }

        // Goal tracking
        const weeklyNet = recentEntries.reduce((sum, e) => sum + e.net, 0);
        const weeklyGoal = data.subscribers.goals.weekly;
        const progress = weeklyNet / weeklyGoal;

        if (progress < 0.5 && recentEntries.length >= 4) {
            recommendations.push({
                priority: 'high',
                text: `Only ${(progress * 100).toFixed(0)}% of weekly goal achieved. Need ${weeklyGoal - weeklyNet} more subscribers in ${7 - recentEntries.length} days.`,
                source: 'Goal tracking'
            });
        }
    }

    // Always show at least one recommendation
    if (recommendations.length === 0) {
        recommendations.push({
            priority: 'low',
            text: 'Maintain current growth rate. Consider exploring new acquisition channels for additional upside.',
            source: '8OWLS baseline recommendation'
        });
    }

    // Store and display
    const synthesisData = loadSynthesisData();
    synthesisData.recommendations = recommendations;
    saveSynthesisData(synthesisData);
    updateRecommendations(recommendations);
}

// ============================================
// EXPORT/IMPORT
// ============================================

function exportData() {
    const data = loadData();
    const entries = data.subscribers.entries;

    if (entries.length === 0) {
        showToast('No data to export');
        return;
    }

    const headers = ['Date', 'New', 'Churned', 'Net', 'Total', 'Notes'];
    const rows = entries.map(e => [
        e.date,
        e.new,
        e.churned,
        e.net,
        e.total,
        e.notes || ''
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brez_growth_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('Data exported successfully');
}

function importCSV(csvData) {
    try {
        const lines = csvData.trim().split('\n');
        const data = loadData();

        lines.forEach(line => {
            const [date, newSubs, churned, total] = line.split(',').map(s => s.trim());
            if (date && !isNaN(parseInt(newSubs))) {
                const net = parseInt(newSubs) - (parseInt(churned) || 0);
                data.subscribers.entries.push({
                    date: date,
                    new: parseInt(newSubs),
                    churned: parseInt(churned) || 0,
                    net: net,
                    total: parseInt(total) || 0,
                    notes: ''
                });
            }
        });

        // Sort by date
        data.subscribers.entries.sort((a, b) => new Date(a.date) - new Date(b.date));

        saveData(data);
        updateStats();
        updateChart(7);
        updateLogTable();
        generateRecommendations();

        showToast('Data imported successfully');
    } catch (error) {
        showToast('Import failed. Check CSV format.');
        console.error('Import error:', error);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatDate(date) {
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function formatDateShort(date) {
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}

function getTimeSince(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function showToast(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #e3f98a, #65cdd8);
        color: #0D0D2A;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 2000;
        animation: toastIn 0.3s ease, toastOut 0.3s ease 2.7s forwards;
    `;

    // Add animation styles
    if (!document.getElementById('toast-styles')) {
        const styles = document.createElement('style');
        styles.id = 'toast-styles';
        styles.textContent = `
            @keyframes toastIn {
                from { opacity: 0; transform: translateX(-50%) translateY(20px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
            @keyframes toastOut {
                from { opacity: 1; transform: translateX(-50%) translateY(0); }
                to { opacity: 0; transform: translateX(-50%) translateY(-20px); }
            }
        `;
        document.head.appendChild(styles);
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function updateNextSynthesisTimer() {
    // Calculate time until next 8-hour synthesis
    const now = new Date();
    const hours = now.getHours();
    const nextSynthesisHour = Math.ceil(hours / 8) * 8;
    const hoursUntil = (nextSynthesisHour - hours) || 8;
    const minutesUntil = 60 - now.getMinutes();

    document.getElementById('nextSynthesis').textContent =
        `${hoursUntil - 1}h ${minutesUntil}m`;
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + S to log data
        if ((e.metaKey || e.ctrlKey) && e.key === 's') {
            e.preventDefault();
            logDailyData();
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            closeSynthesisModal();
            closeTeamModal();
        }

        // Cmd/Ctrl + E to export
        if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
            e.preventDefault();
            exportData();
        }
    });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize chart
    initializeChart();

    // Setup event listeners
    setupInputListeners();
    setupChartControls();
    setupKeyboardShortcuts();

    // Load and display data
    updateStats();
    updateLogTable();
    updateTeamList();
    updateSynthesisPanel();
    generateRecommendations();

    // Start timer updates
    updateNextSynthesisTimer();
    setInterval(updateNextSynthesisTimer, 60000);

    console.log('%c8OWLS Growth Dashboard Initialized',
        'color: #e3f98a; font-size: 14px; font-weight: bold;');
    console.log('%cKeyboard shortcuts: Cmd+S (log), Cmd+E (export), Esc (close modals)',
        'color: #65cdd8; font-size: 12px;');
});
