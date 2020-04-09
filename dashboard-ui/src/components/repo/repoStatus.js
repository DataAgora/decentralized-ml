import React from 'react';
import Reflux from 'reflux';

import CoordinatorStore from './../../stores/CoordinatorStore';
import CoordinatorActions from './../../actions/CoordinatorActions';

class RepoStatus extends Reflux.Component {

  constructor(props) {
    super(props);
    this.store = CoordinatorStore;
  }

  componentDidMount() {
    CoordinatorActions.fetchCoordinatorStatus(this.props.repoId);
  }

  render() {
    const status = this.state.coordinatorStatuses[this.props.repoId];

    switch (status) {
      case "ERROR": return <span className="badge badge-pill badge-danger">Error</span>;
      case "SHUTTING DOWN": return <span className="badge badge-pill badge-danger">Shutting down..</span>;
      case "DEPLOYING": return <span className="badge badge-pill badge-warning">Deploying...</span>;
      case "ACTIVE": return <span className="badge badge-pill badge-success">Active</span>;
      case "IDLE": return <span className="badge badge-pill badge-secondary">Idle</span>;
      default: return <span className="badge badge-pill badge-dark">...</span>;
    }
  }
}

export default RepoStatus;
