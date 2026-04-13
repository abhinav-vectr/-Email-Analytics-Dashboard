/**
 * Email Analytics Dashboard - Main App Component
 * Fetches data from FastAPI backend and displays analytics visualizations
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './App.css';

// Backend API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Color palette for charts
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#a28fd0', '#f48fb1', '#81c784', '#ffb74d'];

function App() {
    // State for all analytics data
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [summary, setSummary] = useState({});
    const [topSenders, setTopSenders] = useState([]);
    const [emailsPerDay, setEmailsPerDay] = useState([]);
    const [emailsPerHour, setEmailsPerHour] = useState([]);
    const [emailsPerWeekday, setEmailsPerWeekday] = useState([]);
    const [domainDistribution, setDomainDistribution] = useState([]);
    const [subjectKeywords, setSubjectKeywords] = useState([]);

    // Fetch all data on component mount
    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch all endpoints in parallel
            const [
                summaryRes,
                topSendersRes,
                emailsPerDayRes,
                emailsPerHourRes,
                emailsPerWeekdayRes,
                domainDistributionRes,
                subjectKeywordsRes
            ] = await Promise.all([
                axios.get(`${API_URL}/summary`),
                axios.get(`${API_URL}/top-senders?limit=10`),
                axios.get(`${API_URL}/emails-per-day`),
                axios.get(`${API_URL}/emails-per-hour`),
                axios.get(`${API_URL}/emails-per-weekday`),
                axios.get(`${API_URL}/domain-distribution`),
                axios.get(`${API_URL}/subject-keywords?limit=15`)
            ]);

            // Update state with fetched data
            setSummary(summaryRes.data);
            setTopSenders(topSendersRes.data);
            setEmailsPerDay(emailsPerDayRes.data);
            setEmailsPerHour(emailsPerHourRes.data);
            setEmailsPerWeekday(emailsPerWeekdayRes.data);
            setDomainDistribution(domainDistributionRes.data);
            setSubjectKeywords(subjectKeywordsRes.data);

            setLoading(false);
        } catch (err) {
            console.error('Error fetching data:', err);
            setError('Failed to load analytics data. Make sure the backend is running on http://localhost:8000');
            setLoading(false);
        }
    };

    // Loading state
    if (loading) {
        return (
            <div className="App">
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading analytics data...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="App">
                <div className="error">
                    <h2>⚠️ Error</h2>
                    <p>{error}</p>
                    <button onClick={fetchAllData}>Retry</button>
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            {/* Header */}
            <header className="header">
                <h1>📧 Email Analytics Dashboard</h1>
                <p>Insights from your Gmail inbox</p>
            </header>

            {/* Summary Cards */}
            <div className="summary-cards">
                <div className="card">
                    <div className="card-icon">📨</div>
                    <div className="card-content">
                        <h3>Total Emails</h3>
                        <p className="card-value">{summary.total_emails?.toLocaleString() || 0}</p>
                    </div>
                </div>

                <div className="card">
                    <div className="card-icon">👥</div>
                    <div className="card-content">
                        <h3>Unique Senders</h3>
                        <p className="card-value">{summary.unique_senders?.toLocaleString() || 0}</p>
                    </div>
                </div>

                <div className="card">
                    <div className="card-icon">📅</div>
                    <div className="card-content">
                        <h3>Days Covered</h3>
                        <p className="card-value">{summary.days_covered || 0}</p>
                    </div>
                </div>

                <div className="card">
                    <div className="card-icon">⭐</div>
                    <div className="card-content">
                        <h3>Top Sender</h3>
                        <p className="card-value-small">{summary.top_sender || 'N/A'}</p>
                        <p className="card-subtext">{summary.top_sender_count || 0} emails</p>
                    </div>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="charts-grid">
                {/* Top Senders Bar Chart */}
                <div className="chart-card">
                    <h2>Top 10 Senders</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={topSenders} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" />
                            <YAxis dataKey="sender" type="category" width={150} />
                            <Tooltip />
                            <Bar dataKey="count" fill="#8884d8" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Emails Per Day Line Chart */}
                <div className="chart-card">
                    <h2>Emails Per Day</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={emailsPerDay}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="count" stroke="#82ca9d" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Emails Per Hour Bar Chart */}
                <div className="chart-card">
                    <h2>Emails by Hour of Day</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={emailsPerHour}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="hour" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#ffc658" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Emails Per Weekday Bar Chart */}
                <div className="chart-card">
                    <h2>Emails by Day of Week</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={emailsPerWeekday}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="day" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#ff7c7c" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Domain Distribution Pie Chart */}
                <div className="chart-card">
                    <h2>Email Domain Distribution</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={domainDistribution}
                                dataKey="count"
                                nameKey="domain"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label={(entry) => entry.domain}
                            >
                                {domainDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Subject Keywords Bar Chart */}
                <div className="chart-card">
                    <h2>Top Subject Keywords</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={subjectKeywords}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="keyword" angle={-45} textAnchor="end" height={100} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#a28fd0" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Footer */}
            <footer className="footer">
                <p>Data range: {summary.first_email ? new Date(summary.first_email).toLocaleDateString() : 'N/A'} - {summary.last_email ? new Date(summary.last_email).toLocaleDateString() : 'N/A'}</p>
            </footer>
        </div>
    );
}

export default App;
