; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c77a58e33_checkpoint_synchronized () Bool)
(declare-fun c77a58e33_claims_unearned_rewards () Bool)
(declare-fun c77a58e33_gauge_is_killed () Bool)
(declare-fun c77a58e33_gauge_is_revived () Bool)
(declare-fun c77a58e33_index_gap_grows () Bool)
(declare-fun c77a58e33_supply_index_frozen_at_prekill () Bool)
(assert
 (= c77a58e33_checkpoint_synchronized c77a58e33_checkpoint_synchronized))
(assert
 (= c77a58e33_claims_unearned_rewards c77a58e33_claims_unearned_rewards))
(assert
 (= c77a58e33_gauge_is_killed c77a58e33_gauge_is_killed))
(assert
 (= c77a58e33_gauge_is_revived c77a58e33_gauge_is_revived))
(assert
 (= c77a58e33_index_gap_grows c77a58e33_index_gap_grows))
(assert
 (= c77a58e33_supply_index_frozen_at_prekill c77a58e33_supply_index_frozen_at_prekill))
(define-fun report_preconditions () Bool (and c77a58e33_gauge_is_killed
     c77a58e33_supply_index_frozen_at_prekill
     c77a58e33_index_gap_grows
     c77a58e33_gauge_is_revived))
(define-fun report_safety () Bool (=> (and c77a58e33_gauge_is_killed
         c77a58e33_supply_index_frozen_at_prekill
         c77a58e33_index_gap_grows
         c77a58e33_gauge_is_revived)
    (or c77a58e33_checkpoint_synchronized
        (not c77a58e33_claims_unearned_rewards))))
(define-fun report_effects () Bool (and c77a58e33_gauge_is_killed
     c77a58e33_supply_index_frozen_at_prekill
     c77a58e33_index_gap_grows
     c77a58e33_gauge_is_revived
     (not (or c77a58e33_checkpoint_synchronized
              (not c77a58e33_claims_unearned_rewards)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
