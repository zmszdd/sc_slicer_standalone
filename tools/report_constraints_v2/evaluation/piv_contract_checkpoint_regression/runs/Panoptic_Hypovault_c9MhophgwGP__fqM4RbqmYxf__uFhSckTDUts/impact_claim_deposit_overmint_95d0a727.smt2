; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca43ea5fc_deposit_overmints_shares () Bool)
(declare-fun ca43ea5fc_ghost_share_count () Int)
(declare-fun ca43ea5fc_total_supply_at_construction () Int)
(assert
 (= ca43ea5fc_deposit_overmints_shares ca43ea5fc_deposit_overmints_shares))
(assert
 (= ca43ea5fc_ghost_share_count ca43ea5fc_ghost_share_count))
(assert
 (= ca43ea5fc_total_supply_at_construction ca43ea5fc_total_supply_at_construction))
(define-fun report_preconditions () Bool (>= ca43ea5fc_total_supply_at_construction ca43ea5fc_ghost_share_count))
(define-fun report_safety () Bool (=> (>= ca43ea5fc_total_supply_at_construction ca43ea5fc_ghost_share_count)
    (not ca43ea5fc_deposit_overmints_shares)))
(define-fun report_effects () Bool (and (>= ca43ea5fc_total_supply_at_construction ca43ea5fc_ghost_share_count)
     (not (not ca43ea5fc_deposit_overmints_shares))))
