class ProfileSettingsModal extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            showCopiedMessage: false,
            confirmLogout: false,
            apiToken: null,
            tokenLoading: false,
            tokenError: null,
            showToken: false,
            confirmRegenerate: false
        };
        this.modalRef = React.createRef();
    }

    componentDidMount() {
        document.addEventListener('keydown', this.handleEscKey);
        // Auto-focus modal for accessibility
        if (this.modalRef.current) {
            this.modalRef.current.focus();
        }
        // Check if user has an API token
        this.checkExistingToken();
    }

    componentWillUnmount() {
        document.removeEventListener('keydown', this.handleEscKey);
    }

    handleEscKey = (e) => {
        if (e.key === 'Escape' && this.props.isOpen) {
            this.props.onClose();
        }
    };

    handleOverlayClick = (e) => {
        if (e.target === e.currentTarget) {
            this.props.onClose();
        }
    };

    checkExistingToken = async () => {
        try {
            const response = await fetch('/auth/token/check', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.has_token) {
                    this.setState({ 
                        apiToken: data.token_preview || 'Token exists (hidden for security)',
                        showToken: false 
                    });
                }
            }
        } catch (error) {
            console.error('Error checking token:', error);
        }
    };

    generateApiToken = async () => {
        if (!this.state.confirmRegenerate && this.state.apiToken) {
            this.setState({ confirmRegenerate: true });
            setTimeout(() => {
                this.setState({ confirmRegenerate: false });
            }, 3000);
            return;
        }

        this.setState({ tokenLoading: true, tokenError: null });
        
        try {
            const response = await fetch('/auth/token/regenerate', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setState({ 
                    apiToken: data.token,
                    showToken: true,
                    confirmRegenerate: false
                });
                
                // Log the token generation
                if (this.props.onTokenGenerated) {
                    this.props.onTokenGenerated();
                }
            } else {
                const error = await response.text();
                this.setState({ tokenError: `Failed to generate token: ${error}` });
            }
        } catch (error) {
            this.setState({ tokenError: `Error: ${error.message}` });
        } finally {
            this.setState({ tokenLoading: false });
        }
    };

    copyApiToken = async () => {
        if (this.state.apiToken && this.state.showToken) {
            try {
                await navigator.clipboard.writeText(this.state.apiToken);
                this.setState({ showCopiedMessage: true });
                setTimeout(() => {
                    this.setState({ showCopiedMessage: false });
                }, 2000);
            } catch (err) {
                console.error('Failed to copy API token:', err);
            }
        }
    };

    handleLogout = async () => {
        if (!this.state.confirmLogout) {
            this.setState({ confirmLogout: true });
            // Reset confirmation state after 3 seconds
            setTimeout(() => {
                this.setState({ confirmLogout: false });
            }, 3000);
            return;
        }

        try {
            const response = await fetch('/auth/logout', {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                // Clear local storage
                localStorage.removeItem('gnosis_auth_code');
                localStorage.removeItem('authStatus');
                
                // Clear auth cookie
                if (window.CookieUtils) {
                    window.CookieUtils.deleteCookie('gnosis_auth_code');
                }
                
                // Close modal and trigger logout in parent
                this.props.onClose();
                if (this.props.onLogout) {
                    this.props.onLogout();
                }
                
                // Reload to reset app state
                window.location.reload();
            }
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    openTokenManager = () => {
        this.props.onClose();
        if (this.props.onOpenTokenManager) {
            this.props.onOpenTokenManager();
        }
    };

    render() {
        if (!this.props.isOpen) return null;

        return React.createElement('div', {
            className: 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4',
            onClick: this.handleOverlayClick,
            'aria-modal': 'true',
            'role': 'dialog',
            'aria-labelledby': 'profile-modal-title'
        },
            React.createElement('div', {
                ref: this.modalRef,
                className: 'bg-gray-900 rounded-lg shadow-xl w-full max-w-md border border-gray-700',
                tabIndex: -1
            },
                // Header
                React.createElement('div', { className: 'flex items-center justify-between p-6 border-b border-gray-700' },
                    React.createElement('h2', { 
                        id: 'profile-modal-title',
                        className: 'text-xl font-semibold text-gray-100' 
                    }, 'Profile Settings'),
                    React.createElement('button', {
                        onClick: this.props.onClose,
                        className: 'text-gray-400 hover:text-gray-200 transition-colors',
                        'aria-label': 'Close modal'
                    },
                        React.createElement('i', { className: 'fas fa-times text-lg' })
                    )
                ),

                // Content
                React.createElement('div', { className: 'p-6 space-y-6' },
                    // User Information Section
                    React.createElement('div', { className: 'space-y-2' },
                        React.createElement('h3', { className: 'text-sm font-medium text-gray-400 uppercase tracking-wider' }, 'User Information'),
                        React.createElement('div', { className: 'flex items-center space-x-3' },
                            React.createElement('div', { className: 'w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center' },
                                React.createElement('i', { className: 'fas fa-user text-gray-400 text-lg' })
                            ),
                            React.createElement('div', null,
                                React.createElement('p', { className: 'text-gray-100 font-medium' }, 'Authenticated User'),
                                React.createElement('p', { className: 'text-sm text-gray-400' }, 'Active Session')
                            )
                        )
                    ),

                    // API Token Section
                    React.createElement('div', { className: 'space-y-3' },
                        React.createElement('h3', { className: 'text-sm font-medium text-gray-400 uppercase tracking-wider' }, 'API Token'),
                        
                        // Token display area
                        this.state.apiToken ? (
                            React.createElement('div', { className: 'space-y-2' },
                                // Token value box
                                React.createElement('div', { className: 'relative' },
                                    React.createElement('div', { 
                                        className: 'bg-gray-800 rounded-lg p-3 pr-12 font-mono text-sm break-all',
                                        style: this.state.showToken ? {} : { filter: 'blur(8px)' }
                                    },
                                        this.state.showToken ? this.state.apiToken : '••••••••••••••••••••••••••••••••'
                                    ),
                                    this.state.showToken && React.createElement('button', {
                                        onClick: this.copyApiToken,
                                        className: 'absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition-colors',
                                        'aria-label': 'Copy API token'
                                    },
                                        React.createElement('i', { className: this.state.showCopiedMessage ? 'fas fa-check text-green-400' : 'fas fa-copy' })
                                    )
                                ),
                                
                                // Token controls
                                React.createElement('div', { className: 'flex items-center justify-between' },
                                    React.createElement('button', {
                                        onClick: () => this.setState({ showToken: !this.state.showToken }),
                                        className: 'text-sm text-gray-400 hover:text-gray-200 transition-colors flex items-center space-x-1'
                                    },
                                        React.createElement('i', { className: this.state.showToken ? 'fas fa-eye-slash' : 'fas fa-eye' }),
                                        React.createElement('span', null, this.state.showToken ? 'Hide token' : 'Show token')
                                    ),
                                    React.createElement('button', {
                                        onClick: this.generateApiToken,
                                        disabled: this.state.tokenLoading,
                                        className: `text-sm ${this.state.confirmRegenerate ? 'text-red-400 hover:text-red-300' : 'text-yellow-400 hover:text-yellow-300'} transition-colors flex items-center space-x-1 disabled:opacity-50`
                                    },
                                        React.createElement('i', { className: this.state.tokenLoading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt' }),
                                        React.createElement('span', null, 
                                            this.state.confirmRegenerate ? 'Click to confirm' : 'Regenerate token'
                                        )
                                    )
                                ),
                                
                                // Messages
                                this.state.showCopiedMessage && React.createElement('p', { className: 'text-sm text-green-400' }, 'Copied to clipboard!'),
                                this.state.confirmRegenerate && React.createElement('p', { className: 'text-sm text-yellow-400' }, 
                                    '⚠️ Warning: Regenerating will invalidate your current token'
                                )
                            )
                        ) : (
                            // No token state
                            React.createElement('div', { className: 'space-y-3' },
                                React.createElement('div', { className: 'bg-gray-800 rounded-lg p-4 text-center' },
                                    React.createElement('p', { className: 'text-gray-400 mb-3' }, 'No API token generated yet'),
                                    React.createElement('button', {
                                        onClick: this.generateApiToken,
                                        disabled: this.state.tokenLoading,
                                        className: 'bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded transition-colors flex items-center space-x-2 mx-auto'
                                    },
                                        this.state.tokenLoading && React.createElement('i', { className: 'fas fa-spinner fa-spin' }),
                                        React.createElement('span', null, this.state.tokenLoading ? 'Generating...' : 'Generate API Token')
                                    )
                                )
                            )
                        ),
                        
                        // Error message
                        this.state.tokenError && React.createElement('div', { 
                            className: 'bg-red-900 bg-opacity-30 border border-red-700 rounded p-3 text-sm text-red-400'
                        }, this.state.tokenError),
                        
                        // API usage info
                        React.createElement('div', { className: 'bg-gray-800 bg-opacity-50 rounded p-3 text-xs text-gray-400' },
                            React.createElement('p', { className: 'font-medium mb-1' }, 'Usage:'),
                            React.createElement('code', { className: 'block bg-black bg-opacity-50 p-2 rounded' },
                                'Authorization: Bearer YOUR_API_TOKEN'
                            )
                        )
                    ),

                    // LLM Configuration Link
                    React.createElement('div', { className: 'space-y-2' },
                        React.createElement('button', {
                            onClick: this.openTokenManager,
                            className: 'w-full bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg p-3 flex items-center justify-between transition-colors'
                        },
                            React.createElement('div', { className: 'flex items-center space-x-3' },
                                React.createElement('i', { className: 'fas fa-brain text-blue-400' }),
                                React.createElement('span', null, 'LLM Configuration')
                            ),
                            React.createElement('i', { className: 'fas fa-chevron-right text-gray-400' })
                        )
                    ),

                    // Logout Section
                    React.createElement('div', { className: 'pt-4 border-t border-gray-700' },
                        React.createElement('button', {
                            onClick: this.handleLogout,
                            className: `w-full ${this.state.confirmLogout ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-800 hover:bg-gray-700'} text-gray-100 rounded-lg p-3 flex items-center justify-center space-x-2 transition-colors`
                        },
                            React.createElement('i', { className: 'fas fa-sign-out-alt' }),
                            React.createElement('span', null, this.state.confirmLogout ? 'Click again to confirm logout' : 'Logout')
                        )
                    )
                )
            )
        );
    }
}

// Export for use in other components
window.ProfileSettingsModal = ProfileSettingsModal;