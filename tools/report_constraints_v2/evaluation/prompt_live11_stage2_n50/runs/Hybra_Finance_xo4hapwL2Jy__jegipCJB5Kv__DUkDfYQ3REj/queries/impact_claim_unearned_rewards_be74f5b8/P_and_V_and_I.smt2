; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c77a58e33_claims_unearned_rewards () Bool)
(declare-fun c77a58e33_gauge_killed_flag () Bool)
(declare-fun c77a58e33_index_gap_grows () Bool)
(declare-fun c77a58e33_revived_without_reset () Bool)
(assert
 (= c77a58e33_claims_unearned_rewards c77a58e33_claims_unearned_rewards))
(assert
 (= c77a58e33_gauge_killed_flag c77a58e33_gauge_killed_flag))
(assert
 (= c77a58e33_index_gap_grows c77a58e33_index_gap_grows))
(assert
 (= c77a58e33_revived_without_reset c77a58e33_revived_without_reset))
(define-fun report_preconditions () Bool (and c77a58e33_gauge_killed_flag
     c77a58e33_index_gap_grows
     c77a58e33_revived_without_reset))
(define-fun report_safety () Bool (=> (and c77a58e33_gauge_killed_flag
         c77a58e33_index_gap_grows
         c77a58e33_revived_without_reset)
    (not c77a58e33_claims_unearned_rewards)))
(define-fun report_effects () Bool (and c77a58e33_gauge_killed_flag
     c77a58e33_index_gap_grows
     c77a58e33_revived_without_reset
     (not (not c77a58e33_claims_unearned_rewards))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
