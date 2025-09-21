// 个人中心页面JavaScript

let currentPage = 1;
let totalPages = 1;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    loadEssayHistory();
});

// 加载用户个人信息
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        if (!response.ok) {
            throw new Error('Failed to load profile');
        }
        
        const profile = await response.json();
        
        // 更新个人信息
        document.getElementById('username').textContent = profile.username;
        document.getElementById('user-email').textContent = profile.email;
        document.getElementById('join-date').textContent = new Date(profile.created_at).toLocaleDateString('zh-CN');
        
        // 更新成就统计
        document.getElementById('overall-average').textContent = profile.stats.average_score;
        document.getElementById('total-essays').textContent = profile.stats.total_essays;
        
        // 更新各项能力分数
        updateRubricScore('task', profile.stats.avg_task_achievement);
        updateRubricScore('coherence', profile.stats.avg_coherence_cohesion);
        updateRubricScore('lexical', profile.stats.avg_lexical_resource);
        updateRubricScore('grammar', profile.stats.avg_grammatical_range_accuracy);
        
    } catch (error) {
        console.error('Error loading profile:', error);
        showError('加载个人信息失败');
    }
}

// 更新各项能力分数显示
function updateRubricScore(type, score) {
    const progressBar = document.getElementById(`${type}-progress`);
    const scoreText = document.getElementById(`${type}-score`);
    
    const percentage = (score / 9.0) * 100;
    progressBar.style.width = `${percentage}%`;
    scoreText.textContent = `${score}/9.0`;
    
    // 根据分数设置颜色
    if (score >= 7) {
        progressBar.style.backgroundColor = '#28a745';
    } else if (score >= 6) {
        progressBar.style.backgroundColor = '#ffc107';
    } else {
        progressBar.style.backgroundColor = '#dc3545';
    }
}

// 加载批改历史
async function loadEssayHistory(page = 1) {
    try {
        const response = await fetch(`/api/user/essays?page=${page}&per_page=10`);
        if (!response.ok) {
            throw new Error('Failed to load essay history');
        }
        
        const data = await response.json();
        
        // 更新分页信息
        currentPage = data.current_page;
        totalPages = data.pages;
        
        // 更新表格内容
        updateHistoryTable(data.essays);
        updatePagination(data);
        
    } catch (error) {
        console.error('Error loading essay history:', error);
        showError('加载批改历史失败');
    }
}

// 更新历史表格
function updateHistoryTable(essays) {
    const tbody = document.getElementById('history-tbody');
    
    if (essays.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">暂无批改记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = essays.map(essay => `
        <tr>
            <td>${essay.created_at}</td>
            <td>IELTS</td>
            <td>${essay.topic}</td>
            <td class="score">${essay.overall_score}</td>
            <td>
                <button class="btn-link" onclick="viewEssayDetail(${essay.id})">
                    查看详情
                </button>
            </td>
        </tr>
    `).join('');
}

// 更新分页控件
function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    
    if (data.pages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一页按钮
    if (data.has_prev) {
        paginationHTML += `<button class="page-btn" onclick="loadEssayHistory(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>`;
    }
    
    // 页码按钮
    for (let i = 1; i <= data.pages; i++) {
        const isActive = i === currentPage ? 'active' : '';
        paginationHTML += `<button class="page-btn ${isActive}" onclick="loadEssayHistory(${i})">${i}</button>`;
    }
    
    // 下一页按钮
    if (data.has_next) {
        paginationHTML += `<button class="page-btn" onclick="loadEssayHistory(${currentPage + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>`;
    }
    
    pagination.innerHTML = paginationHTML;
}

// 查看作文详情
async function viewEssayDetail(essayId) {
    try {
        const response = await fetch(`/api/user/essays/${essayId}`);
        if (!response.ok) {
            throw new Error('Failed to load essay detail');
        }
        
        const essay = await response.json();
        displayEssayDetail(essay);
        document.getElementById('essay-detail-modal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading essay detail:', error);
        showError('加载作文详情失败');
    }
}

// 显示作文详情
function displayEssayDetail(essay) {
    const content = document.getElementById('essay-detail-content');
    
    content.innerHTML = `
        <div class="essay-detail">
            <div class="essay-header">
                <h3>${essay.topic}</h3>
                <div class="essay-meta">
                    <span class="essay-date">${essay.created_at}</span>
                    <span class="essay-score">总分: ${essay.overall_score}</span>
                </div>
            </div>
            
            <div class="essay-content">
                <h4>作文内容</h4>
                <div class="essay-text">${essay.content}</div>
            </div>
            
            <div class="essay-scores">
                <h4>详细评分</h4>
                <div class="score-grid">
                    <div class="score-item">
                        <span class="score-label">Task Achievement</span>
                        <span class="score-value">${essay.rubric_scores.task_achievement}</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Coherence & Cohesion</span>
                        <span class="score-value">${essay.rubric_scores.coherence_cohesion}</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Lexical Resource</span>
                        <span class="score-value">${essay.rubric_scores.lexical_resource}</span>
                    </div>
                    <div class="score-item">
                        <span class="score-label">Grammatical Range</span>
                        <span class="score-value">${essay.rubric_scores.grammatical_range_accuracy}</span>
                    </div>
                </div>
            </div>
            
            <div class="essay-feedback">
                <h4>总体反馈</h4>
                <div class="feedback-text">${essay.overall_feedback}</div>
            </div>
            
            ${essay.grammar_corrections.length > 0 ? `
                <div class="essay-corrections">
                    <h4>语法错误批注</h4>
                    <div class="corrections-list">
                        ${essay.grammar_corrections.map(correction => `
                            <div class="correction-item">
                                <div class="correction-text incorrect">
                                    <i class="fas fa-times"></i> ${correction.incorrect}
                                </div>
                                <div class="correction-text correct">
                                    <i class="fas fa-check"></i> ${correction.correct}
                                </div>
                                <div class="explanation">${correction.explanation}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${essay.vocabulary_improvements.length > 0 ? `
                <div class="essay-improvements">
                    <h4>词汇改进建议</h4>
                    <div class="corrections-list">
                        ${essay.vocabulary_improvements.map(improvement => `
                            <div class="correction-item">
                                <div class="correction-text incorrect">
                                    <i class="fas fa-times"></i> ${improvement.incorrect}
                                </div>
                                <div class="correction-text correct">
                                    <i class="fas fa-check"></i> ${improvement.correct}
                                </div>
                                <div class="explanation">${improvement.explanation}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// 关闭作文详情模态框
function closeEssayDetail() {
    document.getElementById('essay-detail-modal').style.display = 'none';
}

// 刷新历史记录
function refreshHistory() {
    loadEssayHistory(currentPage);
}

// 返回首页
function goHome() {
    window.location.href = '/';
}

// 退出登录
async function logout() {
    try {
        const response = await fetch('/logout');
        if (response.ok) {
            window.location.href = '/';
        } else {
            showError('退出登录失败');
        }
    } catch (error) {
        console.error('Error logging out:', error);
        showError('退出登录失败');
    }
}

// 显示错误信息
function showError(message) {
    alert(message);
}

// 点击模态框外部关闭
window.addEventListener('click', function(event) {
    const modal = document.getElementById('essay-detail-modal');
    if (event.target === modal) {
        closeEssayDetail();
    }
});
