import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:5000/login', { username, password });
      onLogin(res.data.access_token);
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <div className="login-form">
      <h2>智能停车管理系统</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="用户名" onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="密码" onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">登录</button>
      </form>
    </div>
  );
};