import React from 'react';
import { render } from 'react-dom'
import { BrowserRouter } from 'react-router-dom';
import App from './components/app';
import InitializeActions from './actions/initializeActions';
import registerServiceWorker from './utils/registerServiceWorker';

import 'jquery/dist/jquery.js';
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/js/bootstrap.js';


import { library } from '@fortawesome/fontawesome-svg-core'
import { faSignOutAlt, faPlus, faSync } from '@fortawesome/free-solid-svg-icons'

library.add(faPlus, faSignOutAlt, faSync);

InitializeActions.initApp();
render((
  <BrowserRouter>
      <App />
  </BrowserRouter>
), document.getElementById('app'));
registerServiceWorker();
