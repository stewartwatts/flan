functions {
  real term_vol(real annual_vol, real bus_days) {
    return annual_vol * sqrt(bus_days / 251.0);
  }
  vector effective_vol_vec(vector annual_vol, vector event_days, int N) {
    vector[N] adj_vol;
    for (n in 1:N)
      adj_vol[n] <- term_vol(annual_vol[n], event_days[n]);
    return adj_vol;
  }
  real amb_t(real amb_t_minus_1, real mean_vol, real alpha) {
    return alpha * amb_t_minus_1 + (1.0 - alpha) * mean_vol;
  }
  vector amb_t_vec(vector amb_t_minus_1, real mean_vol, real alpha) {
    return alpha * amb_t_minus_1 + (1.0 - alpha) * mean_vol;
  }
}
data {
  int<lower=1> N_obs;
  int<lower=1> horizon_bus_days;
  int<lower=1> N_feats;
  int<lower=1> N_predict_points;

  vector<lower=1>[N_obs] event_days_b;
  vector<lower=1>[horizon_bus_days] event_days_f;

  vector[N_obs] pnl_1d;
  matrix[N_obs, N_feats] pnl_feats;
  row_vector[N_feats] active_feats;
  real<lower=0> beta_prior_sigma;

  real<lower=0> base_vol_prior_mean;
  real<lower=0> base_vol_prior_sigma;
  real<lower=0> vov_prior_mean;
  real<lower=0> vov_prior_sigma;
}
parameters {
  vector[N_feats] pnl_mu_beta;

  vector<lower=0>[N_obs] ambient;
  real<lower=0> base_vol;
  real<lower=0,upper=1> alpha;
  real<lower=0> vov;
}
transformed parameters {
  /* Models MUST have `trade_mu` and `trade_sigma`.
   * StanAnalysis instances look for these parameters for sizing.
   */
  vector[N_obs] eff_vol;
  real trade_mu;
  real<lower=0> trade_sigma;

  eff_vol <- effective_vol_vec(ambient, event_days_b, N_obs);
  trade_mu <- (active_feats * pnl_mu_beta) * horizon_bus_days;
  trade_sigma <- term_vol(amb_t(ambient[N_obs], base_vol, alpha), sum(event_days_f));
}
model {
  alpha ~ beta(2, 1);
  vov ~ normal(vov_prior_mean, vov_prior_sigma);
  ambient[1] ~ normal(base_vol_prior_mean, base_vol_prior_sigma);
  tail(ambient, N_obs - 1) ~ normal(amb_t_vec(head(ambient, N_obs - 1), base_vol, alpha), vov);
  pnl_mu_beta ~ normal(0, beta_prior_sigma);
  pnl_1d ~ normal(pnl_feats * pnl_mu_beta, eff_vol);
}
generated quantities {
  real pnl_pred[N_predict_points];
  for (n in 1:N_predict_points) 
    pnl_pred[n] <- normal_rng(trade_mu, trade_sigma);
}