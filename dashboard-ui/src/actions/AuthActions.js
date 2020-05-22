import Reflux from 'reflux';

var AuthActions = Reflux.createActions({
  login: {children: ['completed', 'failed']},
  registration: {children: ['completed', 'failed']},
  clearError: {},
  logout: {}
});

export default AuthActions;
