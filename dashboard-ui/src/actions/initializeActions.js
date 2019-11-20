import Dispatcher from '../dispatcher/appDispatcher';
import ActionTypes from '../constants/actionTypes';

var InitializeActions = {
  initApp: function() {

    Dispatcher.dispatch({
      actionType: ActionTypes.INITIALIZE,
      initialData: {

      }
    });

  }
};

export default InitializeActions;
