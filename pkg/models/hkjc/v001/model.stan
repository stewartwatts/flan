functions {
  real age_factor(int race_num, vector beta_age_curve) {
    return beta_age_curve[0] + beta_age_curve[1] * race_num + beta_age_curve[2] * race_num * race_num;
  }
}
data {
  int<lower=1> N_horses;
  int<lower=1> N_12_races;
  int<lower=1> N_14_races;

  // horse index
  int<lower=1,upper=N_horses> horse_index_12[N_12_races, 12];
  int<lower=1,upper=N_horses> horse_index_14[N_14_races, 14];

  // each entrant's n-th race data
  int<lower=1> nth_race_12[N_12_races, 12];  
  int<lower=1> nth_race_14[N_14_races, 14];

  // winner index: [1, .., 12] or [1, .. 14]
  int<lower=1,upper=12> winner_12[N_12_races];
  int<lower=1,upper=14> winner_14[N_14_races];
}
parameters {
  vector[N_horses] skills;
  vector[3] beta_age_curve;         // parabolic n-th race adjustment factor
  vector[12] perf_12[N_12_races];   // random performance
  vector[14] perf_14[N_14_races];   // random performance
  real<lower=0> perf_sigma;        
}
transformed parameters {
  // skills
  vector[12] skills_12[N_12_races];
  vector[14] skills_14[N_14_races];

  // race number adjustments
  vector[12] age_adj_12[N_12_races];
  vector[14] age_adj_14[N_14_races];

  // performances
  vector[12] perf_mu_12[N_12_races];
  vector[14] perf_mu_14[N_14_races];

  // skills
  for (i in 1:N_12_races) {
    for (j in 1:12) {
      skills_12[i][j] <- skills[horse_index_12[i, j]];
    }
  }
  for (i in 1:N_14_races) {
    for (j in 1:14) {
      skills_14[i][j] <- skills[horse_index_14[i, j]];
    }
  }

  // race number adjustments
  for (i in 1:N_12_races) {
    for (j in 1:12) {
      age_adj_12[i][j] <- age_factor(nth_race_12[i, j], beta_age_curve);
    }
  }
  for (i in 1:N_14_races) {
    for (j in 1:14) {
      age_adj_14[i][j] <- age_factor(nth_race_14[i, j], beta_age_curve);
    }
  }

  // center of performance distributions
  for (i in 1:N_12_races) {
      perf_mu_12[i] <- skills_12[i] + age_adj_12[i];
  }
  for (i in 1:N_14_races) {
      perf_mu_14[i] <- skills_14[i] + age_adj_14[i];
  }
}
model {
  beta_age_curve[0] ~ normal(0, 5);
  beta_age_curve[1] ~ normal(-15, 10);
  beta_age_curve[2] ~ normal(0, 5);
  skills ~ normal(25, 8.3);
  perf_sigma ~ cauchy(0, 2.5);

  // performances are normally distributed around skill + age adj
  // winners are softmax of performances
  for (n in 1:N_12_races) {
    perf_12[n] ~ normal(perf_mu_12[n], perf_sigma);
    winner_12[n] ~ categorical(softmax(perf_12[n]));
  }
  for (n in 1:N_14_races) {
    perf_14[n] ~ normal(perf_mu_14[n], perf_sigma);
    winner_14[n] ~ categorical(softmax(perf_14[n]));
  }
}