import React from 'react';
import Reflux from 'reflux';
import { Link } from 'react-router-dom';
import AuthStore from './../../stores/AuthStore';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';


import logo from './white-logo.png';
import './header.css';

class Header extends Reflux.Component {
  constructor(props) {
    super(props);
    this.store = AuthStore;
  }

  render() {
    var rightElement;
    if (this.state.isAuthenticated) {
      let companyName = this.state.claims["company"];

      rightElement = (
        <ul className="navbar-nav ml-auto">
          <li className="nav-item">
              <Link to="/new" className="nav-link" href="#"><b>New repo</b></Link>
          </li>
          <li className="nav-item">
              <div className="nav-link">{"@" + companyName}</div>
          </li>
          <li className="nav-item">
              <Link to="/signout" className="nav-link" href="#"><FontAwesomeIcon icon="sign-out-alt" /></Link>
          </li>
        </ul>
      );
    } else {
      rightElement = (
        <ul className="navbar-nav ml-auto">
          <li className="nav-item">
              <Link to="/signin" className="nav-link" href="#"><b>Sign In</b></Link>
          </li>
        </ul>
      );
    }

    return (
      <nav className="navbar navbar-expand-lg navbar-dark margin-bottom">
        <div className="container-fluid">
          <Link to="/" className="navbar-brand">
            <img src={logo} className="header-logo" alt="logo" />
          </Link>

          <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>

          <div id="navbarNav" className="navbar-collapse collapse w-100 order-3 dual-collapse2">
            { rightElement }
          </div>
        </div>
      </nav>
    );
  }
}

export default Header;
