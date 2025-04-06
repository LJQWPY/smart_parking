// 页面加载完成后执行以下代码
window.onload = function () {
    // 获取登录表单元素
    const loginForm = document.getElementById('loginForm');
    // 获取视频监控面板元素
    const videoPanel = document.getElementById('videoPanel');
    // 获取登录容器元素
    const loginContainer = document.getElementById('loginContainer');
    // 获取视频流显示元素
    const videoFeed = document.getElementById('videoFeed');
    // 获取退出登录按钮元素
    const logoutButton = document.getElementById('logoutButton');
    // 获取错误信息提示元素
    const errorMessage = document.getElementById('errorMessage');
    // 获取摄像头开关按钮容器元素
    const cameraList = document.getElementById('cameraList');
    // 获取注册表单元素
    const registerForm = document.getElementById('registerForm');
    // 获取注册容器元素
    const registerContainer = document.getElementById('registerContainer');
    // 获取注册错误信息提示元素
    const regErrorMessage = document.getElementById('regErrorMessage');
    // 获取去注册按钮元素
    const goToRegister = document.getElementById('goToRegister');
    // 获取返回登录按钮元素
    const goToLogin = document.getElementById('goToLogin');

    // 为去注册按钮添加点击事件监听器，点击后隐藏登录容器，显示注册容器
    goToRegister.addEventListener('click', () => {
        loginContainer.classList.add('hidden');
        registerContainer.classList.remove('hidden');
    });

    // 为返回登录按钮添加点击事件监听器，点击后隐藏注册容器，显示登录容器
    goToLogin.addEventListener('click', () => {
        registerContainer.classList.add('hidden');
        loginContainer.classList.remove('hidden');
    });

    // 为登录表单添加提交事件监听器
    loginForm.addEventListener('submit', async (e) => {
        // 阻止表单默认提交行为
        e.preventDefault();
        // 获取用户名输入框的值
        const username = document.getElementById('username').value;
        // 获取密码输入框的值
        const password = document.getElementById('password').value;

        // 检查用户名和密码是否为空
        if (!username || !password) {
            errorMessage.textContent = '用户名和密码不能为空';
            errorMessage.classList.remove('hidden');
            return;
        }

        try {
            // 发送登录请求到后端
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error(`网络请求失败，状态码: ${response.status}`);
            }

            // 解析响应数据
            const data = await response.json();
            if (data.access_token) {
                // 若登录成功，隐藏登录容器，显示视频监控面板，隐藏错误信息提示
                loginContainer.classList.add('hidden');
                videoPanel.classList.remove('hidden');
                errorMessage.classList.add('hidden');

                // 打印发送的 JWT 令牌，方便调试
                console.log(`发送的 JWT 令牌: ${data.access_token}`);

                // 创建事件源，用于接收视频流数据
                const eventSource = new EventSource('/video_feed', {
                    headers: {
                        'Authorization': `Bearer ${data.access_token}`
                    }
                });

                // 当接收到视频流数据时，更新视频流显示元素的src属性
                eventSource.onmessage = (event) => {
                    const frameData = event.data.split('data: ')[1];
                    videoFeed.src = `data:image/jpeg;base64,${frameData}`;
                };

                // 当事件源出错时，显示错误提示，隐藏视频监控面板，显示登录容器
                eventSource.onerror = () => {
                    alert('视频流获取失败，请稍后重试');
                    videoPanel.classList.add('hidden');
                    loginContainer.classList.remove('hidden');
                };

                // 获取可用摄像头数量并创建开关按钮
                const numCameras = Object.keys(window.camera_manager?.cameras || {}).length;
                for (let i = 0; i < numCameras; i++) {
                    const button = document.createElement('button');
                    button.textContent = `摄像头 ${i + 1} 开启`;
                    button.dataset.camId = i;
                    button.classList.add('bg-blue-500', 'text-white', 'p-2', 'rounded', 'hover:bg-blue-600', 'mt-2', 'mr-2');
                    // 为开关按钮添加点击事件监听器
                    button.addEventListener('click', async () => {
                        const camId = parseInt(button.dataset.camId);
                        try {
                            // 发送摄像头开关控制请求到后端
                            const response = await fetch('/toggle_camera', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${data.access_token}`
                                },
                                body: JSON.stringify({ cam_id: camId })
                            });

                            if (!response.ok) {
                                throw new Error(`网络请求失败，状态码: ${response.status}`);
                            }

                            const result = await response.json();
                            if (result.msg === 'Camera toggled successfully') {
                                // 根据操作结果更新按钮文本
                                if (button.textContent.includes('开启')) {
                                    button.textContent = `摄像头 ${i + 1} 关闭`;
                                } else {
                                    button.textContent = `摄像头 ${i + 1} 开启`;
                                }
                            }
                        } catch (error) {
                            alert(`网络请求出错，请稍后重试: ${error.message}`);
                        }
                    });
                    // 将开关按钮添加到摄像头开关按钮容器中
                    cameraList.appendChild(button);
                }
            } else {
                // 若登录失败，显示错误信息提示
                errorMessage.textContent = data.msg;
                errorMessage.classList.remove('hidden');
            }
        } catch (error) {
            alert(`网络请求出错，请稍后重试: ${error.message}`);
        }
    });

    // 为注册表单添加提交事件监听器
    registerForm.addEventListener('submit', async (e) => {
        // 阻止表单默认提交行为
        e.preventDefault();
        // 获取注册用户名输入框的值
        const regUsername = document.getElementById('regUsername').value;
        // 获取注册密码输入框的值
        const regPassword = document.getElementById('regPassword').value;

        // 检查用户名和密码是否为空
        if (!regUsername || !regPassword) {
            regErrorMessage.textContent = '用户名和密码不能为空';
            regErrorMessage.classList.remove('hidden');
            return;
        }

        try {
            // 发送注册请求到后端
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: regUsername, password: regPassword })
            });

            if (!response.ok) {
                throw new Error(`网络请求失败，状态码: ${response.status}`);
            }

            // 解析响应数据
            const data = await response.json();
            if (data.status === 201) {
                // 若注册成功，提示用户注册成功并返回登录页面
                alert('注册成功，请登录');
                registerContainer.classList.add('hidden');
                loginContainer.classList.remove('hidden');
            } else {
                // 若注册失败，显示错误信息提示
                regErrorMessage.textContent = data.msg;
                regErrorMessage.classList.remove('hidden');
            }
        } catch (error) {
            alert(`网络请求出错，请稍后重试: ${error.message}`);
        }
    });

    // 为退出登录按钮添加点击事件监听器，点击后隐藏视频监控面板，显示登录容器
    logoutButton.addEventListener('click', () => {
        videoPanel.classList.add('hidden');
        loginContainer.classList.remove('hidden');
    });
};    