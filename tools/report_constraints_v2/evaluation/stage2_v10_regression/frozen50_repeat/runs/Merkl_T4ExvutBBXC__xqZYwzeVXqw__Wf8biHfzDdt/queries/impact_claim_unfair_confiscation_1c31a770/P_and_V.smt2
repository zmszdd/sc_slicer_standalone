; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca1d82f93_bond_confiscated_to_governor () Bool)
(declare-fun ca1d82f93_bond_posted () Bool)
(declare-fun ca1d82f93_bond_refunded_to_disputer () Bool)
(declare-fun ca1d82f93_dispute_valid () Bool)
(declare-fun ca1d82f93_disputer_blacklisted () Bool)
(assert
 (= ca1d82f93_bond_confiscated_to_governor ca1d82f93_bond_confiscated_to_governor))
(assert
 (= ca1d82f93_bond_posted ca1d82f93_bond_posted))
(assert
 (= ca1d82f93_bond_refunded_to_disputer ca1d82f93_bond_refunded_to_disputer))
(assert
 (= ca1d82f93_dispute_valid ca1d82f93_dispute_valid))
(assert
 (= ca1d82f93_disputer_blacklisted ca1d82f93_disputer_blacklisted))
(define-fun report_preconditions () Bool (and ca1d82f93_bond_posted
     ca1d82f93_dispute_valid
     ca1d82f93_disputer_blacklisted))
(define-fun report_safety () Bool (=> (and ca1d82f93_bond_posted
         ca1d82f93_dispute_valid
         ca1d82f93_disputer_blacklisted)
    (and ca1d82f93_bond_refunded_to_disputer
         (not ca1d82f93_bond_confiscated_to_governor))))
(define-fun report_effects () Bool (and ca1d82f93_bond_posted
     ca1d82f93_dispute_valid
     ca1d82f93_disputer_blacklisted
     (not (and ca1d82f93_bond_refunded_to_disputer
               (not ca1d82f93_bond_confiscated_to_governor)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
