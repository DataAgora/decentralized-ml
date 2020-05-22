import React, { Component } from 'react';
import { Link } from 'react-router-dom';

class NotFoundPage extends Component {
  render() {
      return (
        <div className="text-center">
          <h1>Searching For Repo...</h1>
          <p>If this is your repo, it will be available shortly.</p>
          <p><Link to="/">Back to Home</Link></p>
        </div>
      );
  }
}

export default NotFoundPage;
