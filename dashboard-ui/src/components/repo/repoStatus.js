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

    if (status === undefined) {
      return <span className="badge badge-pill badge-dark">...</span>
    }

    if (!("Busy" in status)) {
      if (this.props.isDeploying) {
        return <span className="badge badge-pill badge-warning">Deploying...</span>
      } else {
        return <span className="badge badge-pill badge-danger">Unknown</span>
      }
    }

    if (status["Busy"] === true) {
      return <span className="badge badge-pill badge-success">Active</span>
    } else {
      return <span className="badge badge-pill badge-secondary">Idle</span>;
    }
  }
}

export default RepoStatus;
