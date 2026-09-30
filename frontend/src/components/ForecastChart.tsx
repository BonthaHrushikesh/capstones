import { EnergyChart } from './index';

export function ForecastChart({ actual = [], forecast = [], anomalies = [], height = 300 }) {
  return <EnergyChart data={{ actual, forecast }} anomalies={anomalies} height={height}/>;
}
