import React, { Component } from 'react';
import { Link } from 'react-router-dom';

class RepoLogs extends Component {

  render() {
    let content;
    if (this.props.logs.length === 0) {
      content = (
        <div>
          <p className="card-text"><b>No model has been trained yet.</b></p>
          <Link to="/explora" className="btn btn-dark mt-2">Train a new model</Link>
        </div>
      );
    } else {
      content = (

        <table className="table table-striped">
          <thead>
            <tr>
              <th scope="col">SessionId</th>
              <th scope="col">Time</th>
              <th scope="col">Action</th>
              <th scope="col">Log Content</th>
            </tr>
          </thead>
          <tbody>

            {this.props.logs.map((log, index) => {
              return <tr key={index}>
                <th scope="row">{log.SessionId}</th>
                <td>{this._formatTime(log.CreationTime)}</td>
                <td>{log.ContentType}</td>
                <td>{log.Content}</td>
              </tr>
            })}
          </tbody>
        </table>
      );
    }

    return (
      <div className="row mt-5">
        <div className="col-1"></div>
        <div className="col-10">
        <div className="card">
          <div className="card-header">
            <h5>Logs</h5>
            <p className="mb-0"><small>History of training sessions for this repo. You can debug your environment from here.</small></p>
          </div>
          <div className="card-body text-center mt-3">
            {content}
          </div>
        </div>
        </div>
      </div>
    )
  }

  _formatTime(timestamp) {
    var t = new Date(timestamp * 1000);
    return t.toISOString();
  }
}

export default RepoLogs;
