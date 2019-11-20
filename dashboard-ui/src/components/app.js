/*eslint-disable strict */ // Disabling check because we can't run strict mode. Need global vars.
import React, { Component } from 'react'
import Header from './common/header';
import Routes from './../routes';

import './common/app.css';

class App extends Component {
  render() {
    return (
      <div>
        <Header />
        <div className="container-fluid">
          <Routes />
        </div>
      </div>
    );
  }
}

export default App;
