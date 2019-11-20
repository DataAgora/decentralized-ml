import Reflux from 'reflux';

var AuthActions = Reflux.createActions({
  login: {children: ['completed', 'failed']},
  registration: {children: ['completed', 'failed']},
  logout: {}
});

export default AuthActions;
