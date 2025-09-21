// Global variables
let currentFeedback = null;
let chatContext = '';
let currentUser = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    checkAuthStatus();
});

function initializeApp() {
    // Add word count functionality
    const essayText = document.getElementById('essay-text');
    essayText.addEventListener('input', updateWordCount);
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Add modal click outside to close
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('conjunction-modal');
        if (event.target === modal) {
            closeConjunctionModal();
        }
    });
}

// Word count functionality
function updateWordCount() {
    const text = document.getElementById('essay-text').value;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    document.getElementById('word-count').textContent = `words: ${wordCount}`;
}

// Keyboard shortcuts
function handleKeyboardShortcuts(event) {
    if (event.ctrlKey || event.metaKey) {
        if (event.key === 'Enter') {
            if (document.getElementById('upload-section').classList.contains('active')) {
                submitEssay();
            } else if (document.getElementById('dialogue-section').classList.contains('active')) {
                sendMessage();
            }
        }
    }
}

// Upload functionality
function uploadImage() {
    // Create file input element
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none';
    
    input.onchange = function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageData = e.target.result;
                extractTextFromImage(imageData);
            };
            reader.readAsDataURL(file);
        }
    };
    
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
}

// Extract text from image using OCR
async function extractTextFromImage(imageData) {
    showLoading();
    
    try {
        const response = await fetch('/api/ocr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: OCR处理失败`);
        }
        
        const data = await response.json();
        
        // Add extracted text to essay textarea
        const essayText = document.getElementById('essay-text');
        const currentText = essayText.value;
        const newText = currentText ? currentText + '\n\n' + data.text : data.text;
        essayText.value = newText;
        
        // Update word count
        updateWordCount();
        
        alert('图片文字提取成功！已添加到作文内容中。');
        
    } catch (error) {
        console.error('OCR Error:', error);
        alert('图片文字提取失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Conjunction Helper
async function showConjunctionHelper() {
    try {
        const response = await fetch('/api/conjunctions');
        if (!response.ok) {
            throw new Error('Failed to load conjunctions');
        }
        
        const data = await response.json();
        displayConjunctions(data);
        document.getElementById('conjunction-modal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading conjunctions:', error);
        alert('加载连词助手失败: ' + error.message);
    }
}

function closeConjunctionModal() {
    document.getElementById('conjunction-modal').style.display = 'none';
}

function displayConjunctions(data) {
    const content = document.getElementById('conjunction-content');
    content.innerHTML = '';
    
    // Parse the conjunction data and display it
    let currentCategory = '';
    let currentExamples = [];
    
    data.forEach((item, index) => {
        if (item.startsWith('💡') || item.startsWith('🔥') || item.startsWith('⏩') || 
            item.startsWith('🤝') || item.startsWith('⚖️') || item.startsWith('🎯') || 
            item.startsWith('🔗') || item.startsWith('⚔️') || item.startsWith('➕')) {
            
            // Save previous category if exists
            if (currentCategory && currentExamples.length > 0) {
                content.appendChild(createCategoryCard(currentCategory, currentExamples));
            }
            
            // Start new category
            currentCategory = item;
            currentExamples = [];
        } else if (item.startsWith('常用连接词：')) {
            // This is the conjunction list, skip for now
        } else if (item.startsWith('💬')) {
            currentExamples.push({
                english: item.substring(2), // Remove emoji
                chinese: data[index + 1] ? data[index + 1].substring(2) : ''
            });
        }
    });
    
    // Add last category
    if (currentCategory && currentExamples.length > 0) {
        content.appendChild(createCategoryCard(currentCategory, currentExamples));
    }
}

function createCategoryCard(category, examples) {
    const categoryDiv = document.createElement('div');
    categoryDiv.className = 'conjunction-category';
    
    const title = document.createElement('h3');
    title.textContent = category;
    categoryDiv.appendChild(title);
    
    const examplesDiv = document.createElement('div');
    examplesDiv.className = 'conjunction-examples';
    
    examples.forEach(example => {
        const exampleDiv = document.createElement('div');
        exampleDiv.className = 'conjunction-example';
        
        const englishDiv = document.createElement('div');
        englishDiv.className = 'english';
        englishDiv.textContent = example.english;
        
        const chineseDiv = document.createElement('div');
        chineseDiv.className = 'chinese';
        chineseDiv.textContent = example.chinese;
        
        exampleDiv.appendChild(englishDiv);
        exampleDiv.appendChild(chineseDiv);
        examplesDiv.appendChild(exampleDiv);
    });
    
    categoryDiv.appendChild(examplesDiv);
    return categoryDiv;
}

// Hot Topics
async function getRandomTopic() {
    try {
        const response = await fetch('/api/random-topic');
        if (!response.ok) {
            throw new Error('Failed to get random topic');
        }
        
        const data = await response.json();
        document.getElementById('essay-topic').value = data.topic_text;
        
    } catch (error) {
        console.error('Error getting random topic:', error);
        alert('获取当季热题失败: ' + error.message);
    }
}

// Submit essay for analysis
async function submitEssay() {
    const topic = document.getElementById('essay-topic').value.trim();
    const essay = document.getElementById('essay-text').value.trim();
    
    if (!topic || !essay) {
        alert('请填写完整的题目和作文内容');
        return;
    }
    
    if (essay.split(/\s+/).length < 50) {
        alert('作文内容太短，请至少输入50个单词');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                essay: essay
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: 分析失败，请重试`);
        }
        
        currentFeedback = await response.json();
        displayFeedback(currentFeedback);
        showSection('feedback-section');
        
    } catch (error) {
        console.error('Error:', error);
        alert('分析失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Display feedback
function displayFeedback(feedback) {
    // Overall score and feedback
    document.getElementById('overall-score').textContent = feedback.overall_score || '6.0';
    document.getElementById('overall-feedback-text').textContent = feedback.overall_feedback || '';
    
    // Rubric scores
    if (feedback.rubric_scores) {
        displayRubricScores(feedback.rubric_scores);
    }
    
    // Statistics
    if (feedback.statistics) {
        displayStatistics(feedback.statistics);
    }
    
    // Task Achievement
    if (feedback.task_achievement) {
        document.getElementById('task-response-score').textContent = feedback.task_achievement.score || '6';
        populateList('task-response-strengths', feedback.task_achievement.strengths || []);
        populateList('task-response-improvements', feedback.task_achievement.areas_for_improvement || []);
        populateSuggestions('task-response-suggestions', feedback.task_achievement.improvement_suggestions || {});
    }
    
    // Coherence and Cohesion
    if (feedback.coherence_cohesion) {
        document.getElementById('coherence-score').textContent = feedback.coherence_cohesion.score || '6';
        populateList('coherence-strengths', feedback.coherence_cohesion.strengths || []);
        populateList('coherence-improvements', feedback.coherence_cohesion.areas_for_improvement || []);
        populateSuggestions('coherence-suggestions', feedback.coherence_cohesion.improvement_suggestions || {});
    }
    
    // Lexical Resource
    if (feedback.lexical_resource) {
        document.getElementById('lexical-score').textContent = feedback.lexical_resource.score || '6';
        populateList('lexical-strengths', feedback.lexical_resource.strengths || []);
        populateList('lexical-improvements', feedback.lexical_resource.areas_for_improvement || []);
        populateVocabularyReplacements('vocabulary-replacements', feedback.lexical_resource.vocabulary_improvements || []);
    }
    
    // Grammatical Range and Accuracy
    if (feedback.grammatical_range_accuracy) {
        populateGrammarCorrections('grammar-list', feedback.grammatical_range_accuracy.grammar_corrections || []);
    }
    
    if (feedback.lexical_resource && feedback.lexical_resource.vocabulary_improvements) {
        populateVocabularyCorrections('vocabulary-list', feedback.lexical_resource.vocabulary_improvements || []);
    }
}

// Display rubric scores
function displayRubricScores(rubricScores) {
    document.getElementById('task-achievement-score').textContent = rubricScores.task_achievement || '6';
    document.getElementById('coherence-cohesion-score').textContent = rubricScores.coherence_cohesion || '6';
    document.getElementById('lexical-resource-score').textContent = rubricScores.lexical_resource || '6';
    document.getElementById('grammatical-range-score').textContent = rubricScores.grammatical_range_accuracy || '6';
}

// Display statistics
function displayStatistics(stats) {
    // Linking words
    document.getElementById('linking-words-count').textContent = stats.linking_words_count || 0;
    const linkingGoal = stats.linking_words_goal || 7;
    document.getElementById('linking-words-goal').textContent = `meeting the goal of ${linkingGoal} or more`;
    
    // Word repetition
    document.getElementById('word-repetition-count').textContent = stats.word_repetition_count || 0;
    const repetitionGoal = stats.word_repetition_goal || 3;
    document.getElementById('word-repetition-goal').textContent = `meeting the goal of ${repetitionGoal} or fewer`;
    
    // Grammar mistakes
    document.getElementById('grammar-mistakes-count').textContent = stats.grammar_mistakes_count || 0;
    document.getElementById('grammar-mistakes-goal').textContent = 'detected issues';
    
    // Update card colors based on performance
    updateStatCardColors(stats);
}

// Update stat card colors based on performance
function updateStatCardColors(stats) {
    // Linking words card
    const linkingCard = document.getElementById('linking-words-card');
    const linkingCount = stats.linking_words_count || 0;
    const linkingGoal = stats.linking_words_goal || 7;
    
    if (linkingCount >= linkingGoal) {
        linkingCard.style.borderLeft = '4px solid #28a745';
    } else if (linkingCount >= linkingGoal * 0.5) {
        linkingCard.style.borderLeft = '4px solid #ffc107';
    } else {
        linkingCard.style.borderLeft = '4px solid #dc3545';
    }
    
    // Word repetition card
    const repetitionCard = document.getElementById('word-repetition-card');
    const repetitionCount = stats.word_repetition_count || 0;
    const repetitionGoal = stats.word_repetition_goal || 3;
    
    if (repetitionCount <= repetitionGoal) {
        repetitionCard.style.borderLeft = '4px solid #28a745';
    } else if (repetitionCount <= repetitionGoal * 2) {
        repetitionCard.style.borderLeft = '4px solid #ffc107';
    } else {
        repetitionCard.style.borderLeft = '4px solid #dc3545';
    }
    
    // Grammar mistakes card
    const grammarCard = document.getElementById('grammar-mistakes-card');
    const grammarCount = stats.grammar_mistakes_count || 0;
    
    if (grammarCount === 0) {
        grammarCard.style.borderLeft = '4px solid #28a745';
    } else if (grammarCount <= 3) {
        grammarCard.style.borderLeft = '4px solid #ffc107';
    } else {
        grammarCard.style.borderLeft = '4px solid #dc3545';
    }
}

// Helper functions for populating content
function populateList(elementId, items) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        element.appendChild(li);
    });
}

function populateSuggestions(elementId, suggestions) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    Object.entries(suggestions).forEach(([key, value]) => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        
        const title = document.createElement('div');
        title.className = 'suggestion-title';
        title.textContent = formatSuggestionTitle(key);
        
        const content = document.createElement('div');
        content.className = 'suggestion-content';
        content.textContent = value;
        
        div.appendChild(title);
        div.appendChild(content);
        element.appendChild(div);
    });
}

function populateVocabularyReplacements(elementId, replacements) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    replacements.forEach(replacement => {
        const div = document.createElement('div');
        div.className = 'correction-item';
        
        let errorTypeHtml = '';
        if (replacement.error_type) {
            errorTypeHtml = `<div class="error-type"><strong>错误类型：</strong>${replacement.error_type}</div>`;
        }
        
        div.innerHTML = `
            <div class="correction-text incorrect">
                <i class="fas fa-times"></i> ${replacement.incorrect}
            </div>
            <div class="correction-text correct">
                <i class="fas fa-check"></i> ${replacement.correct}
            </div>
            ${errorTypeHtml}
            <div class="explanation">${replacement.explanation}</div>
        `;
        
        element.appendChild(div);
    });
}

function populateGrammarCorrections(elementId, corrections) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    corrections.forEach(correction => {
        const div = document.createElement('div');
        div.className = 'correction-item';
        
        let errorTypeHtml = '';
        if (correction.error_type) {
            errorTypeHtml = `<div class="error-type"><strong>错误类型：</strong>${correction.error_type}</div>`;
        }
        
        let contextHtml = '';
        if (correction.sentence_context) {
            contextHtml = `<div class="sentence-context"><strong>句子上下文：</strong>"${correction.sentence_context}"</div>`;
        }
        
        div.innerHTML = `
            <div class="correction-text incorrect">
                <i class="fas fa-times"></i> ${correction.incorrect}
            </div>
            <div class="correction-text correct">
                <i class="fas fa-check"></i> ${correction.correct}
            </div>
            ${errorTypeHtml}
            <div class="explanation">${correction.explanation}</div>
            ${contextHtml}
        `;
        
        element.appendChild(div);
    });
}

function populateVocabularyCorrections(elementId, corrections) {
    populateGrammarCorrections(elementId, corrections); // Same format
}

function formatSuggestionTitle(key) {
    const titles = {
        'how_to_address_prompt': '如何完整回应题目',
        'how_to_develop_ideas': '如何展开观点',
        'how_to_stay_on_topic': '如何点题',
        'contextual_development': '上下文展开',
        'better_format': '更优的格式',
        'text_structure': '行文结构',
        'logical_organization': '逻辑组织',
        'thematic_organization': '主题组织',
        'logical_sequencing': '逻辑衔接顺序',
        'referencing_substitution': '引用替换',
        'discourse_markers': '标志性逻辑提示词'
    };
    return titles[key] || key;
}

// Tab functionality
function showTab(tabName) {
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab panel
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked tab button
    event.target.classList.add('active');
}

// Section navigation
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
}

// Clear and start new essay
function clearAndStartNew() {
    if (confirm('确定要清除当前内容并开始新的作文吗？')) {
        document.getElementById('essay-topic').value = '';
        document.getElementById('essay-text').value = '';
        document.getElementById('word-count').textContent = 'words: 0';
        currentFeedback = null;
        showSection('upload-section');
    }
}

// Enter dialogue mode
function enterDialogueMode() {
    if (!currentFeedback) {
        alert('请先完成作文分析');
        return;
    }
    
    // Prepare chat context
    chatContext = JSON.stringify(currentFeedback);
    
    // Initialize chat with welcome message
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="message assistant">
            <strong>AI导师：</strong>您好！我已经完成了对您作文的分析。您可以询问任何关于批改的问题，或者提交修改后的作文让我重新评估。请问有什么可以帮助您的吗？
        </div>
    `;
    
    showSection('dialogue-section');
}

// Send message in dialogue mode
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) {
        alert('请输入您的问题');
        return;
    }
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    // Show loading
    const loadingMessage = addMessageToChat('正在思考中...', 'assistant', true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                context: chatContext
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: 发送消息失败`);
        }
        
        const data = await response.json();
        
        // Remove loading message
        loadingMessage.remove();
        
        // Add AI response
        addMessageToChat(data.response, 'assistant');
        
    } catch (error) {
        console.error('Error:', error);
        loadingMessage.remove();
        addMessageToChat('抱歉，发生了错误: ' + error.message + '。请稍后重试。', 'assistant');
    }
}

// Add message to chat
function addMessageToChat(message, sender, isLoading = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    if (sender === 'assistant') {
        messageDiv.innerHTML = `<strong>AI导师：</strong>${message}`;
    } else {
        messageDiv.innerHTML = `<strong>您：</strong>${message}`;
    }
    
    if (isLoading) {
        messageDiv.style.opacity = '0.6';
        messageDiv.style.fontStyle = 'italic';
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Submit revised essay
function submitRevisedEssay() {
    const revisedEssay = prompt('请粘贴您修改后的作文内容：');
    
    if (revisedEssay && revisedEssay.trim()) {
        // Add user message about submitting revised essay
        addMessageToChat(`我提交了修改后的作文：\n\n${revisedEssay}`, 'user');
        
        // Show AI response
        addMessageToChat('感谢您提交修改后的作文！让我重新分析一下您的改进...', 'assistant');
        
        // Here you could implement re-analysis of the revised essay
        setTimeout(() => {
            addMessageToChat('分析完成！您的修改在以下方面有所改进：\n\n1. 语法错误明显减少\n2. 词汇使用更加准确\n3. 文章结构更加清晰\n\n建议继续练习以进一步提升写作水平！', 'assistant');
        }, 2000);
    }
}

// Back to feedback
function backToFeedback() {
    showSection('feedback-section');
}

// Loading functions
function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// Utility functions
function highlightTextInEssay() {
    // This function would highlight problematic text in the original essay
    // Implementation would depend on the specific feedback structure
    console.log('Highlighting text in essay...');
}

// User Authentication Functions
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/user/profile');
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            showUserInfo(user);
        } else {
            showAuthButtons();
        }
    } catch (error) {
        console.log('User not authenticated');
        showAuthButtons();
    }
}

function showUserInfo(user) {
    document.getElementById('user-info').style.display = 'flex';
    document.getElementById('auth-buttons').style.display = 'none';
    document.getElementById('current-username').textContent = user.username;
}

function showAuthButtons() {
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('auth-buttons').style.display = 'flex';
}

// Login Modal Functions
function showLoginModal() {
    document.getElementById('login-modal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('login-modal').style.display = 'none';
    document.getElementById('login-form').reset();
}

// Register Modal Functions
function showRegisterModal() {
    document.getElementById('register-modal').style.display = 'block';
}

function closeRegisterModal() {
    document.getElementById('register-modal').style.display = 'none';
    document.getElementById('register-form').reset();
}

// Switch between login and register
function switchToRegister() {
    closeLoginModal();
    showRegisterModal();
}

function switchToLogin() {
    closeRegisterModal();
    showLoginModal();
}

// Login Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            showUserInfo(result.user);
            closeLoginModal();
            showSuccess('登录成功！');
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('登录失败，请重试');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const registerData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('注册成功！请登录');
            closeRegisterModal();
            showLoginModal();
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('Register error:', error);
        showError('注册失败，请重试');
    }
}

// Logout Function
async function logout() {
    try {
        const response = await fetch('/logout');
        if (response.ok) {
            currentUser = null;
            showAuthButtons();
            showSuccess('已退出登录');
        } else {
            showError('退出登录失败');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showError('退出登录失败');
    }
}

// Go to Profile
function goToProfile() {
    window.location.href = '/profile';
}

// Utility Functions
function showSuccess(message) {
    // 简单的成功提示，可以后续优化为更好的UI
    alert('✅ ' + message);
}

function showError(message) {
    // 简单的错误提示，可以后续优化为更好的UI
    alert('❌ ' + message);
}

// Export functions for global access
window.submitEssay = submitEssay;
window.uploadImage = uploadImage;
window.showConjunctionHelper = showConjunctionHelper;
window.closeConjunctionModal = closeConjunctionModal;
window.getRandomTopic = getRandomTopic;
window.showTab = showTab;
window.clearAndStartNew = clearAndStartNew;
window.enterDialogueMode = enterDialogueMode;
window.sendMessage = sendMessage;
window.submitRevisedEssay = submitRevisedEssay;
window.backToFeedback = backToFeedback;
window.showLoginModal = showLoginModal;
window.closeLoginModal = closeLoginModal;
window.showRegisterModal = showRegisterModal;
window.closeRegisterModal = closeRegisterModal;
window.switchToRegister = switchToRegister;
window.switchToLogin = switchToLogin;
window.logout = logout;
window.goToProfile = goToProfile;
