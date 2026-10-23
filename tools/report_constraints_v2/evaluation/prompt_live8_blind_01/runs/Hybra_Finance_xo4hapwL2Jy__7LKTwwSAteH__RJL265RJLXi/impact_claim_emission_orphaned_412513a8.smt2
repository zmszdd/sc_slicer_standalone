; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca6bfe57d_emission_indexed () Bool)
(declare-fun ca6bfe57d_emission_orphaned_on_balance () Bool)
(declare-fun ca6bfe57d_total_weight_is_zero () Bool)
(assert
 (= ca6bfe57d_emission_indexed ca6bfe57d_emission_indexed))
(assert
 (= ca6bfe57d_emission_orphaned_on_balance ca6bfe57d_emission_orphaned_on_balance))
(assert
 (= ca6bfe57d_total_weight_is_zero ca6bfe57d_total_weight_is_zero))
(define-fun report_preconditions () Bool ca6bfe57d_total_weight_is_zero)
(define-fun report_safety () Bool (=> ca6bfe57d_total_weight_is_zero
    (and ca6bfe57d_emission_indexed
         (not ca6bfe57d_emission_orphaned_on_balance))))
(define-fun report_effects () Bool (and ca6bfe57d_total_weight_is_zero
     (not (and ca6bfe57d_emission_indexed
               (not ca6bfe57d_emission_orphaned_on_balance)))))
