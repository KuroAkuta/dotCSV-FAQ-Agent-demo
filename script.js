document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const csvUpload = document.getElementById('csv-upload');
    const deleteCSVButton = document.getElementById('delete-csv');
    const reloadVectorDBButton = document.getElementById('reload-vectordb');
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    const notificationClose = document.getElementById('notification-close');
    const confirmDialog = document.getElementById('confirm-dialog');
    const confirmMessage = document.getElementById('confirm-message');
    const confirmCancel = document.getElementById('confirm-cancel');
    const confirmOk = document.getElementById('confirm-ok');

    // API URL - 根据实际部署情况修改
    // 默认假设前端和后端部署在同一域名下
    // 如果部署在不同域名或端口，请修改为完整URL，例如：http://localhost:8000/ask
    const API_URL = 'http://127.0.0.1:8000/ask';
    const UPLOAD_CSV_URL = 'http://127.0.0.1:8000/upload-csv';
    const DELETE_CSV_URL = 'http://127.0.0.1:8000/delete-csv';
    const RELOAD_VECTORDB_URL = 'http://127.0.0.1:8000/reload-vectordb';

    // 自动调整输入框高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight > 120 ? 120 : userInput.scrollHeight) + 'px';
    });

    // 按Enter发送消息（Shift+Enter换行）
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 点击发送按钮
    sendButton.addEventListener('click', sendMessage);

    // 创建消息元素
    function createMessageElement(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';

        const icon = document.createElement('i');
        icon.className = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatar.appendChild(icon);

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const contentDiv = document.createElement('div');
        
        // 如果是用户消息，直接显示文本
        // 如果是机器人消息，渲染为Markdown
        if (sender === 'user') {
            const paragraph = document.createElement('p');
            paragraph.textContent = text;
            contentDiv.appendChild(paragraph);
        } else {
            // 对于机器人消息，我们创建一个空的div，稍后会填充Markdown内容
            contentDiv.className = 'markdown-content';
            if (text) {
                contentDiv.innerHTML = marked.parse(text);
            }
        }
        
        messageContent.appendChild(contentDiv);

        // 对于用户消息，头像放在右边
        // 对于机器人消息，头像放在左边
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        return messageDiv;
    }

    // 发送消息函数
    async function sendMessage() {
        const message = userInput.value.trim();

        // 如果消息为空，不发送
        if (!message) return;

        // 添加用户消息到聊天界面
        addMessage(message, 'user');

        // 清空输入框并重置高度
        userInput.value = '';
        userInput.style.height = 'auto';

        // 禁用发送按钮
        sendButton.disabled = true;

        // 显示加载指示器
        showTypingIndicator();

        try {
            // 创建一个消息元素，用于流式显示AI回答
            const messageDiv = createMessageElement('', 'bot');
            const markdownContent = messageDiv.querySelector('.message-content .markdown-content');
            
            // 移除加载指示器
            removeTypingIndicator();
            
            // 添加消息元素到聊天界面
            chatMessages.appendChild(messageDiv);
            
            // 滚动到最新消息
            scrollToBottom();
            
            // 发送请求到后端API并处理流式响应
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input: message }),
            });
            
            // 检查响应状态
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // 获取响应的可读流
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let partialText = '';
            
            // 读取流数据
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                // 解码接收到的数据
                const text = decoder.decode(value, { stream: true });
                partialText += text;
                
                // 更新消息内容，将Markdown转换为HTML
                markdownContent.innerHTML = marked.parse(partialText);
                
                // 处理代码块的语法高亮
                document.querySelectorAll('pre code').forEach((block) => {
                    if (window.hljs) {
                        window.hljs.highlightBlock(block);
                    }
                });
                
                // 滚动到最新消息
                scrollToBottom();
            }
            
        } catch (error) {
            console.error('Error:', error);
            
            // 移除加载指示器
            removeTypingIndicator();
            
            // 显示错误消息
            addMessage('抱歉，发生了错误，请稍后再试。', 'bot');
        } finally {
            // 启用发送按钮
            sendButton.disabled = false;
        }
    }

    // 添加消息到聊天界面
    function addMessage(text, sender) {
        const messageDiv = createMessageElement(text, sender);
        chatMessages.appendChild(messageDiv);
        
        // 滚动到最新消息
        scrollToBottom();
    }

    // 显示正在输入指示器
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-container';
        typingDiv.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'avatar';

        const icon = document.createElement('i');
        icon.className = 'fas fa-robot';
        avatar.appendChild(icon);

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingIndicator.appendChild(dot);
        }

        typingDiv.appendChild(avatar);
        typingDiv.appendChild(typingIndicator);

        chatMessages.appendChild(typingDiv);

        // 滚动到最新消息
        scrollToBottom();
    }

    // 移除正在输入指示器
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // 滚动到最新消息
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 显示通知
    function showNotification(message, type = 'info') {
        notificationMessage.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        // 5秒后自动隐藏
        setTimeout(() => {
            hideNotification();
        }, 5000);
    }

    // 隐藏通知
    function hideNotification() {
        notification.classList.remove('show');
    }

    // 显示确认对话框
    function showConfirmDialog(message, onConfirm) {
        confirmMessage.textContent = message;
        confirmDialog.classList.add('show');
        
        // 存储确认回调
        confirmOk.onclick = () => {
            hideConfirmDialog();
            onConfirm();
        };
    }

    // 隐藏确认对话框
    function hideConfirmDialog() {
        confirmDialog.classList.remove('show');
    }

    // 上传CSV文件
    async function uploadCSV(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(UPLOAD_CSV_URL, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showNotification(`CSV文件上传成功，共包含${result.document_count}条记录`, 'success');
                // 添加系统消息
                addMessage('知识库已更新，您可以开始提问了！', 'bot');
            } else {
                showNotification(`上传失败: ${result.detail || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('上传CSV时出错:', error);
            showNotification('上传失败，请检查服务器连接', 'error');
        }
    }

    // 删除CSV文件
    async function deleteCSV() {
        try {
            const response = await fetch(DELETE_CSV_URL, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showNotification('知识库已重置', 'success');
                // 添加系统消息
                addMessage('知识库已重置，AI助手将无法回答特定问题，直到上传新的知识库。', 'bot');
            } else {
                showNotification(`删除失败: ${result.detail || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('删除CSV时出错:', error);
            showNotification('删除失败，请检查服务器连接', 'error');
        }
    }

    // 事件监听器
    // 上传CSV文件
    csvUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
                uploadCSV(file);
            } else {
                showNotification('请上传CSV格式的文件', 'error');
            }
            // 重置文件输入，以便可以再次选择同一文件
            csvUpload.value = '';
        }
    });

    // 删除CSV文件
    deleteCSVButton.addEventListener('click', () => {
        showConfirmDialog('确定要删除知识库吗？这将移除所有已上传的数据。', deleteCSV);
    });

    // 关闭通知
    notificationClose.addEventListener('click', hideNotification);

    // 取消确认对话框
    confirmCancel.addEventListener('click', hideConfirmDialog);
});