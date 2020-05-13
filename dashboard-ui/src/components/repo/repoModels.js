import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import Reflux from 'reflux';
import AuthStore from './../../stores/AuthStore';
import Endpoints from './../../constants/endpoints.js';


class RepoModels extends Reflux.Component {

  constructor(props) {
    super(props);
  }

  _downloadModel(log) {
    let round = JSON.parse(log.Content)["round"];
    let session_id = JSON.parse(log.Content)["session_id"];
    let repo_id = log.RepoId;

    let jwtString = AuthStore.state.jwt;
    fetch(
      Endpoints["dashboardGetDownloadModelURL"],
      {
        method: 'POST',
        headers: {
          'Content-Type':'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer ' + jwtString,
        },
        body: JSON.stringify({
          "RepoId": repo_id,
          "SessionId": session_id,
          "Round": round,
        })
      }
    ).then(response => {
      response.json().then(res => {
        let url = res['message'];
        this._openInNewTab(url);
      })
    });
  }

  _openInNewTab(url) {
    var win = window.open(url, '_blank');
    win.focus();
  }

  render() {
    let content;
    let logs = this.props.logs;
    if (logs == undefined || logs.length === 0) {
      content = (
        <div>
          <p className="card-text"><b>No model has been trained yet.</b></p>
        </div>
      );
    } else {
      content = (

        <table className="table table-striped">
          <thead>
            <tr>
              <th scope="col">SessionId</th>
              <th scope="col">Round</th>
              <th scope="col">Time</th>
              <th scope="col">Download Model</th>
            </tr>
          </thead>
          <tbody>

            {logs.map((log, index) => {
              return <tr key={index}>
                <th scope="row">{log.SessionId}</th>
                <td>{JSON.parse(log.Content).round}</td>
                <td>{this._formatTime(log.CreationTime)}</td>
                <td>
                  <a href="#download-model" className="btn btn-xs btn-primary ml-2" onClick={this._downloadModel.bind(this, log)}>Download</a>
                </td>
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
            <h5>Model Hub</h5>
            <p className="mb-0"><small>Download your resulting models from here.</small></p>
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

export default RepoModels;
