; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d2696a6_battle_result_processed_occurred () Bool)
(declare-fun c9d2696a6_better_party_rating_decreased () Bool)
(declare-fun c9d2696a6_dependent_data_incorrect () Bool)
(declare-fun c9d2696a6_negative_is_false () Bool)
(declare-fun c9d2696a6_negative_is_true () Bool)
(declare-fun c9d2696a6_worse_party_rating_increased () Bool)
(assert
 (= c9d2696a6_battle_result_processed_occurred c9d2696a6_battle_result_processed_occurred))
(assert
 (= c9d2696a6_better_party_rating_decreased c9d2696a6_better_party_rating_decreased))
(assert
 (= c9d2696a6_dependent_data_incorrect c9d2696a6_dependent_data_incorrect))
(assert
 (= c9d2696a6_negative_is_false c9d2696a6_negative_is_false))
(assert
 (= c9d2696a6_negative_is_true c9d2696a6_negative_is_true))
(assert
 (= c9d2696a6_worse_party_rating_increased c9d2696a6_worse_party_rating_increased))
(define-fun report_preconditions () Bool (and c9d2696a6_battle_result_processed_occurred
     c9d2696a6_negative_is_true
     c9d2696a6_negative_is_false))
(define-fun report_safety () Bool (=> (and c9d2696a6_battle_result_processed_occurred
         (or c9d2696a6_negative_is_true c9d2696a6_negative_is_false))
    (and (not c9d2696a6_better_party_rating_decreased)
         (not c9d2696a6_worse_party_rating_increased)
         (not c9d2696a6_dependent_data_incorrect))))
(define-fun report_effects () Bool (and c9d2696a6_battle_result_processed_occurred
     (or c9d2696a6_negative_is_true c9d2696a6_negative_is_false)
     (not (and (not c9d2696a6_better_party_rating_decreased)
               (not c9d2696a6_worse_party_rating_increased)
               (not c9d2696a6_dependent_data_incorrect)))))
