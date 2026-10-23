; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cebd599ac_index_gap_grows () Bool)
(declare-fun cebd599ac_revived_without_reset () Bool)
(declare-fun cebd599ac_supply_index_frozen () Bool)
(declare-fun cebd599ac_unearned_epoch_count () Int)
(assert
 (= cebd599ac_index_gap_grows cebd599ac_index_gap_grows))
(assert
 (= cebd599ac_revived_without_reset cebd599ac_revived_without_reset))
(assert
 (= cebd599ac_supply_index_frozen cebd599ac_supply_index_frozen))
(assert
 (= cebd599ac_unearned_epoch_count cebd599ac_unearned_epoch_count))
(define-fun report_preconditions () Bool (and cebd599ac_supply_index_frozen
     cebd599ac_index_gap_grows
     cebd599ac_revived_without_reset))
(define-fun report_safety () Bool (=> (and cebd599ac_supply_index_frozen
         cebd599ac_index_gap_grows
         cebd599ac_revived_without_reset)
    (= 0 cebd599ac_unearned_epoch_count)))
(define-fun report_effects () Bool (and cebd599ac_supply_index_frozen
     cebd599ac_index_gap_grows
     cebd599ac_revived_without_reset
     (not (= 0 cebd599ac_unearned_epoch_count))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
