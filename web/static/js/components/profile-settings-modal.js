class ProfileSettingsModal extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            showCopiedMessage: false,
            confirmLogout: false,
            tokens: [],
            tokenLoading: false,
            tokenError: null,
            showCreateForm: false,
            newTokenName: '',
            newTokenCreated: null,
            tokensLoading: false,
            tokenJustCreated: false,  // Add flag to track if token was just created
            deleteConfirmations: {}   // Track delete confirmations for each token
        };
        this.modalRef = React.createRef();
    }

    componentDidMount() {
        document.addEventListener('keydown', this.handleEscKey);
        // Auto-focus modal for accessibility
        if (this.modalRef.current) {
            this.modalRef.current.focus();
        }
        // Load user's API tokens
        this.loadTokens();
    }

    componentDidUpdate(prevProps) {
        // Reset tokenJustCreated flag when modal is reopened
        if (this.props.isOpen && !prevProps.isOpen) {
            this.setState({ 
                tokenJustCreated: false,
                newTokenCreated: null,
                showCreateForm: false,
                newTokenName: '',
                tokenError: null,
                deleteConfirmations: {}  // Reset all delete confirmations
            });
            // Reload tokens when modal opens
            this.loadTokens();
        }
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

    loadTokens = async () => {
        this.setState({ tokensLoading: true });
        try {
            console.log('Loading API tokens...');
            const response = await fetch('/auth/tokens', {
                method: 'GET',
                credentials: 'include'
            });
            
            console.log('Token response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Token data received:', data);
                this.setState({ tokens: data.tokens || [] });
            } else {
                const errorText = await response.text();
                console.error('Token loading failed:', response.status, errorText);
            }
        } catch (error) {
            console.error('Error loading tokens:', error);
        } finally {
            this.setState({ tokensLoading: false });
        }
    };

    createApiToken = async () => {
        if (!this.state.newTokenName.trim()) {
            this.setState({ tokenError: 'Please enter a token name' });
            return;
        }

        this.setState({ tokenLoading: true, tokenError: null });
        
        try {
            console.log('Creating API token with name:', this.state.newTokenName);
            const response = await fetch('/auth/tokens', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: this.state.newTokenName
                })
            });
            
            console.log('Create token response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Token created:', data);
                this.setState({ 
                    newTokenCreated: data.token,
                    showCreateForm: false,
                    newTokenName: '',
                    tokenJustCreated: true  // Set flag when token is created
                });
                
                // Reload tokens
                this.loadTokens();
                
                // Log the token generation
                if (this.props.onTokenGenerated) {
                    this.props.onTokenGenerated();
                }
            } else {
                const error = await response.json();
                console.error('Token creation failed:', error);
                this.setState({ tokenError: error.error || 'Failed to generate token' });
            }
        } catch (error) {
            console.error('Token creation error:', error);
            this.setState({ tokenError: `Error: ${error.message}` });
        } finally {
            this.setState({ tokenLoading: false });
        }
    };

    deleteToken = async (tokenId) => {
        try {
            const response = await fetch(`/auth/tokens/${tokenId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                this.loadTokens();
            }
        } catch (error) {
            console.error('Failed to delete token:', error);
        }
    };

    copyToken = async (token) => {
        try {
            await navigator.clipboard.writeText(token);
            this.setState({ showCopiedMessage: true });
            setTimeout(() => {
                this.setState({ showCopiedMessage: false });
            }, 2000);
        } catch (err) {
            console.error('Failed to copy token:', err);
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
            className: 'fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4',
            onClick: this.handleOverlayClick,
            'aria-modal': 'true',
            'role': 'dialog',
            'aria-labelledby': 'profile-modal-title'
        },
            React.createElement('div', {
                ref: this.modalRef,
                className: 'bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl border border-gray-700',
                tabIndex: -1
            },
                // Header
                React.createElement('div', { className: 'flex items-center justify-between p-6 border-b border-gray-700' },
                    React.createElement('div', { className: 'flex items-center space-x-2' },
                        React.createElement('i', { className: 'fas fa-user-circle text-purple-400' }),
                        React.createElement('h2', { 
                            id: 'profile-modal-title',
                            className: 'text-xl font-bold text-purple-400' 
                        }, 'Profile Settings')
                    ),
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
                        React.createElement('div', { className: 'bg-gray-800 rounded-lg p-4' },
                            React.createElement('div', { className: 'flex items-center space-x-4' },
                                React.createElement('div', { className: 'w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center' },
                                    React.createElement('i', { className: 'fas fa-user text-gray-400 text-lg' })
                                ),
                                React.createElement('div', null,
                                    React.createElement('p', { className: 'text-sm text-gray-500 mb-1' }, 
                                        'Name'
                                    ),
                                    React.createElement('p', { className: 'text-lg text-gray-100 font-medium' }, 
                                        this.props.userName || 'Anonymous User'
                                    )
                                )
                            )
                        )
                    ),

                    // API Token Section
                    React.createElement('div', { className: 'space-y-3' },
                        React.createElement('div', { className: 'flex items-center justify-between mb-2' },
                            React.createElement('h3', { className: 'text-sm font-medium text-gray-400 uppercase tracking-wider' }, 'API Tokens'),
                            React.createElement('button', {
                                onClick: () => this.setState({ showCreateForm: true, tokenError: null }),
                                className: `text-sm px-3 py-1 rounded transition-colors ${
                                    this.state.tokenJustCreated 
                                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                                        : 'bg-green-600 hover:bg-green-700 text-white'
                                }`,
                                disabled: this.state.tokenJustCreated
                            }, this.state.tokenJustCreated ? 'Token Created' : 'Create New Token')
                        ),
                        
                        // Token created warning
                        this.state.newTokenCreated && React.createElement('div', { 
                            className: 'bg-green-900 bg-opacity-30 border border-green-700 rounded p-3 text-sm' 
                        },
                            React.createElement('p', { className: 'text-green-400 font-semibold mb-2' }, '⚠️ Copy this token now - it won\'t be shown again!'),
                            React.createElement('div', { className: 'flex items-center space-x-2' },
                                React.createElement('code', { className: 'bg-gray-800 p-2 rounded flex-1 font-mono text-xs text-gray-100' }, this.state.newTokenCreated),
                                React.createElement('button', {
                                    onClick: () => {
                                        this.copyToken(this.state.newTokenCreated);
                                    },
                                    className: 'bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm'
                                }, 'Copy')
                            )
                        ),
                        
                        // Create form
                        this.state.showCreateForm && React.createElement('div', { className: 'bg-gray-800 rounded-lg p-3' },
                            React.createElement('input', {
                                type: 'text',
                                value: this.state.newTokenName,
                                onChange: (e) => this.setState({ newTokenName: e.target.value }),
                                placeholder: 'Token name (e.g., Production API)',
                                className: 'w-full bg-gray-700 text-gray-100 px-3 py-2 rounded mb-2'
                            }),
                            React.createElement('div', { className: 'flex space-x-2' },
                                React.createElement('button', {
                                    onClick: this.createApiToken,
                                    disabled: this.state.tokenLoading,
                                    className: 'bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-3 py-1 rounded text-sm'
                                }, this.state.tokenLoading ? 'Creating...' : 'Create'),
                                React.createElement('button', {
                                    onClick: () => this.setState({ showCreateForm: false, newTokenName: '', tokenError: null }),
                                    className: 'bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm'
                                }, 'Cancel')
                            )
                        ),
                        
                        // Token list
                        React.createElement('div', { 
                            className: 'max-h-48 overflow-y-auto space-y-2 bg-gray-800 rounded-lg p-2',
                            style: { scrollbarWidth: 'thin' }
                        },
                            this.state.tokensLoading ? (
                                React.createElement('p', { className: 'text-gray-400 text-center py-4' }, 'Loading tokens...')
                            ) : this.state.tokens.length === 0 && !this.state.newTokenCreated ? (
                                React.createElement('p', { className: 'text-gray-400 text-center py-4' }, 'No API tokens yet')
                            ) : this.state.tokens.length === 0 && this.state.newTokenCreated ? (
                                React.createElement('p', { className: 'text-gray-400 text-center py-4' }, 'Token created! Copy it above before closing.')
                            ) : (
                                this.state.tokens.map(token => 
                                    React.createElement('div', { 
                                        key: token.token_id,
                                        className: 'flex items-center justify-between bg-gray-700 rounded p-2'
                                    },
                                        React.createElement('div', { className: 'flex-1' },
                                            React.createElement('p', { className: 'text-gray-100 text-sm font-medium' }, token.name),
                                            React.createElement('p', { className: 'text-gray-400 text-xs font-mono' }, 
                                                token.token_display || 'Token ID: ' + token.token_id
                                            ),
                                            React.createElement('p', { className: 'text-gray-400 text-xs' }, 
                                                `Last used: ${token.last_used ? new Date(token.last_used).toLocaleDateString() : 'Never'}`
                                            )
                                        ),
                                        React.createElement('button', {
                                            onClick: () => {
                                                const tokenId = token.token_id;
                                                if (this.state.deleteConfirmations[tokenId]) {
                                                    // Second click - actually delete
                                                    this.deleteToken(tokenId);
                                                    // Clear confirmation state
                                                    const newConfirmations = {...this.state.deleteConfirmations};
                                                    delete newConfirmations[tokenId];
                                                    this.setState({ deleteConfirmations: newConfirmations });
                                                } else {
                                                    // First click - set confirmation state
                                                    const newConfirmations = {...this.state.deleteConfirmations};
                                                    newConfirmations[tokenId] = true;
                                                    this.setState({ deleteConfirmations: newConfirmations });
                                                    
                                                    // Reset confirmation after 3 seconds
                                                    setTimeout(() => {
                                                        const currentConfirmations = {...this.state.deleteConfirmations};
                                                        delete currentConfirmations[tokenId];
                                                        this.setState({ deleteConfirmations: currentConfirmations });
                                                    }, 3000);
                                                }
                                            },
                                            className: `w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ${
                                                this.state.deleteConfirmations[token.token_id]
                                                    ? 'bg-red-600 hover:bg-red-700 text-white'
                                                    : 'bg-gray-700 hover:bg-red-600 text-gray-400 hover:text-white'
                                            }`,
                                            title: this.state.deleteConfirmations[token.token_id] 
                                                ? 'Click again to confirm deletion' 
                                                : 'Delete token'
                                        }, 
                                            React.createElement('i', { 
                                                className: `fas ${
                                                    this.state.deleteConfirmations[token.token_id] 
                                                        ? 'fa-exclamation-triangle' 
                                                        : 'fa-times'
                                                } text-sm` 
                                            })
                                        )
                                    )
                                )
                            )
                        ),
                        
                        // Error message
                        this.state.tokenError && React.createElement('div', { 
                            className: 'bg-red-900 bg-opacity-30 border border-red-700 rounded p-3 text-sm text-red-400'
                        }, this.state.tokenError),
                        
                        // Copied message
                        this.state.showCopiedMessage && React.createElement('p', { className: 'text-sm text-green-400 text-center' }, 'Copied to clipboard!')
                    ),

                    // Bottom buttons
                    React.createElement('div', { className: 'pt-4 border-t border-gray-700 flex space-x-3' },
                        // LLM Configuration
                        React.createElement('button', {
                            onClick: this.openTokenManager,
                            className: 'flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-3 flex items-center justify-center space-x-2 transition-colors'
                        },
                            React.createElement('i', { className: 'fas fa-brain' }),
                            React.createElement('span', null, 'LLM Configuration')
                        ),
                        
                        // Logout
                        React.createElement('button', {
                            onClick: this.handleLogout,
                            className: `flex-1 ${this.state.confirmLogout ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'} text-white rounded-lg p-3 flex items-center justify-center space-x-2 transition-colors`
                        },
                            React.createElement('i', { className: 'fas fa-sign-out-alt' }),
                            React.createElement('span', null, this.state.confirmLogout ? 'Confirm Logout' : 'Logout')
                        )
                    )
                )
            )
        );
    }
}

// Export for use in other components
window.ProfileSettingsModal = ProfileSettingsModal;