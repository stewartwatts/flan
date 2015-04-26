functions {
  vector age_factors(vector race_nums, vector beta_age_curve) {
    return beta_age_curve[0] + beta_age_curve[1] * race_nums + beta_age_curve[2] * race_nums .* race_nums;
  }
}
data {
  int N_horses;
  int N_12_races;
  int N_14_races;

  // horse index
  int horse_index_12[N_12_races, 12];
  int horse_index_14[N_14_races, 14];

  // each entrant's n-th race data
  int nth_race_12[N_12_races, 12];  
  int nth_race_14[N_14_races, 14];

  // winner index: [1, .., 12] or [1, .. 14]
  int winner_12[N_12_races];
  int winner_14[N_14_races];
}
parameters {
  vector[N_horses] skills;
  vector[3] beta_age_curve;    // parabolic n-th race adjustment factor
}
transformed parameters {
  vector[12] skills_12[N_12_races];
  vector[14] skills_14[N_14_races];

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
}
model {
  beta_age_curve ~ normal(0, 5);
  skills ~ normal(25, 8.3);

  for (n in 1:N_12_races) {
    winner_12[n] ~ categorical(softmax(skills_12[n]));
  }
  for (n in 1:N_14_races) {
    winner_14[n] ~ categorical(softmax(skills_14[n]));
  }
}